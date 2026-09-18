import json
from datetime import date, timedelta

from odoo.tests import HttpCase, tagged

from .common import SigningKeyMixin
from ..models.license_signer import _workspace_message


@tagged('post_install', '-at_install')
class TestWorkspaceCheck(SigningKeyMixin, HttpCase):

    def _check(self, **params):
        body = {'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}
        r = self.url_open('/techrise/workspace/check', data=json.dumps(body),
                          headers={'Content-Type': 'application/json'})
        self.assertEqual(r.status_code, 200)
        return r.json()['result']

    def test_unknown_uuid_starts_trial(self):
        res = self._check(db_uuid='u-1', server_url='https://nova.odoo.com', db_name='nova',
                          company_name='Nova General Contracting', app_id='techrise_hr',
                          app_version='2.0.0')
        self.assertTrue(res['verified'])
        self.assertEqual(res['status'], 'trial')
        self.assertEqual(res['company'], 'Nova General Contracting')
        self.assertEqual(res['days_left'], 30)
        self.assertFalse(res['read_only'])
        self.assertEqual(res['ends'], (date.today() + timedelta(days=30)).isoformat())
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-1')])
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws.check_count, 1)
        self.assertEqual(ws.server_url, 'https://nova.odoo.com')
        self.assertIn('2.0.0', ws.app_versions)

    def test_response_is_signed_and_verifiable(self):
        res = self._check(db_uuid='u-2', company_name='X')
        self.assertSigned(_workspace_message('u-2', 'trial', res['ends'], res['iat']), res['sig'])

    def test_second_check_touches_not_recreates(self):
        self._check(db_uuid='u-3', company_name='X')
        res = self._check(db_uuid='u-3', company_name='X renamed')
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-3')])
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws.check_count, 2)
        self.assertEqual(res['company'], 'X renamed')

    def test_expired_trial_is_read_only(self):
        self.env['techrise.workspace'].create({
            'name': 'Old', 'db_uuid': 'u-4',
            'trial_start': date.today() - timedelta(days=40),
            'trial_end': date.today() - timedelta(days=5)})
        res = self._check(db_uuid='u-4')
        self.assertTrue(res['verified'])
        self.assertEqual(res['status'], 'expired')
        self.assertTrue(res['read_only'])
        self.assertEqual(res['days_left'], 0)

    def test_active_perpetual(self):
        self.env['techrise.workspace'].create({'name': 'Act', 'db_uuid': 'u-5', 'state': 'active'})
        res = self._check(db_uuid='u-5')
        self.assertEqual(res['status'], 'active')
        self.assertEqual(res['ends'], '')
        self.assertEqual(res['days_left'], -1)

    def test_blocked_not_verified(self):
        self.env['techrise.workspace'].create({'name': 'Bad', 'db_uuid': 'u-6', 'state': 'blocked'})
        res = self._check(db_uuid='u-6')
        self.assertFalse(res['verified'])
        self.assertEqual(res['status'], 'blocked')

    def test_missing_uuid(self):
        res = self._check(company_name='X')
        self.assertFalse(res['verified'])
        self.assertEqual(res['reason'], 'missing_db_uuid')

    # -- hardening (review findings) -------------------------------------
    def test_non_string_payload_does_not_raise(self):
        res = self._check(db_uuid=123, company_name=42, server_url=None,
                          db_name=['x'], app_version=7)
        self.assertEqual(res['status'], 'trial')
        self.assertEqual(res['db_uuid'], '123')
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', '123')])
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws.name, '42')
        self.assertIn('7', ws.app_versions)

    def test_long_values_are_capped(self):
        res = self._check(db_uuid='u-7', company_name='N' * 5000, db_name='D' * 5000,
                          server_url='https://x/' + 'u' * 5000, app_version='v' * 5000)
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-7')])
        self.assertEqual(len(ws.name), 255)
        self.assertEqual(len(res['company']), 255)
        self.assertEqual(len(ws.db_name), 255)
        self.assertEqual(len(ws.server_url), 1024)
        self.assertEqual(len(ws.app_versions), 255)

    def test_app_versions_keep_last_20_distinct(self):
        for i in range(25):
            self._check(db_uuid='u-8', app_version='1.0.%d' % i)
        self._check(db_uuid='u-8', app_version='1.0.24')  # repeat: no duplicate
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-8')])
        versions = ws.app_versions.split(',')
        self.assertEqual(len(versions), 20)
        self.assertEqual(len(set(versions)), 20)
        self.assertNotIn('1.0.0', versions)
        self.assertIn('1.0.24', versions)
        self.assertEqual(ws.check_count, 26)

    def test_app_version_commas_stripped(self):
        self._check(db_uuid='u-9', app_version='2,0,0')
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-9')])
        self.assertEqual(ws.app_versions, '200')

    def test_public_check_creates_no_chatter(self):
        self._check(db_uuid='u-10', company_name='Quiet')
        self._check(db_uuid='u-10', company_name='Quiet renamed')
        ws = self.env['techrise.workspace'].search([('db_uuid', '=', 'u-10')])
        self.assertEqual(ws.name, 'Quiet renamed')
        self.assertFalse(ws.message_ids)
        self.assertFalse(ws.message_follower_ids)
