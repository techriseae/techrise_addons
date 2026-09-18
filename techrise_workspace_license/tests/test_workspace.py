from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestWorkspaceStatus(TransactionCase):

    def _ws(self, **vals):
        base = {'db_uuid': 'uuid-%s' % (self.env['techrise.workspace'].search_count([]) + 1),
                'name': 'Nova'}
        base.update(vals)
        return self.env['techrise.workspace'].create(base)

    def test_create_defaults_to_trial_with_30_day_clock(self):
        ws = self._ws()
        self.assertEqual(ws.state, 'trial')
        self.assertEqual(ws.trial_start, date.today())
        self.assertEqual(ws.trial_end, date.today() + timedelta(days=30))
        self.assertEqual(ws._effective_status(), 'trial')
        self.assertEqual(ws._ends_date(), ws.trial_end)
        self.assertEqual(ws._days_left(date.today()), 30)

    def test_trial_days_param_is_honoured(self):
        self.env['ir.config_parameter'].sudo().set_param('techrise_workspace.trial_days', '14')
        ws = self._ws()
        self.assertEqual(ws.trial_end, date.today() + timedelta(days=14))

    def test_trial_past_end_is_expired(self):
        ws = self._ws(trial_start=date.today() - timedelta(days=40),
                      trial_end=date.today() - timedelta(days=10))
        self.assertEqual(ws._effective_status(), 'expired')
        self.assertEqual(ws._days_left(date.today()), 0)

    def test_active_without_end_is_active_forever(self):
        ws = self._ws()
        ws.action_activate()
        self.assertEqual(ws.state, 'active')
        self.assertEqual(ws._effective_status(), 'active')
        self.assertFalse(ws._ends_date())
        self.assertEqual(ws._days_left(date.today()), -1)

    def test_active_past_licence_end_is_expired(self):
        ws = self._ws(state='active', licence_end=date.today() - timedelta(days=1))
        self.assertEqual(ws._effective_status(), 'expired')

    def test_blocked_wins(self):
        ws = self._ws(state='active')
        ws.action_block()
        self.assertEqual(ws._effective_status(), 'blocked')

    @mute_logger('odoo.sql_db')
    def test_db_uuid_unique(self):
        self._ws(db_uuid='same')
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self._ws(db_uuid='same')

    def test_cron_expire_writes_state(self):
        ws = self._ws(trial_start=date.today() - timedelta(days=40),
                      trial_end=date.today() - timedelta(days=10))
        self.env['techrise.workspace']._cron_expire()
        self.assertEqual(ws.state, 'expired')

    def test_cron_expired_active_licence_ends_on_licence_end(self):
        licence_end = date.today() - timedelta(days=1)
        ws = self._ws(state='active', licence_end=licence_end)
        self.env['techrise.workspace']._cron_expire()
        self.assertEqual(ws.state, 'expired')
        self.assertEqual(ws._ends_date(), licence_end)

    def test_reset_to_trial_restarts_clock(self):
        ws = self._ws(trial_start=date.today() - timedelta(days=40),
                      trial_end=date.today() - timedelta(days=10))
        self.assertEqual(ws._effective_status(), 'expired')
        ws.action_reset_to_trial()
        self.assertEqual(ws.state, 'trial')
        self.assertEqual(ws.trial_end, date.today() + timedelta(days=30))
        self.assertEqual(ws._effective_status(), 'trial')
        self.assertEqual(ws._days_left(date.today()), 30)

    def test_reset_to_trial_clears_licence_end(self):
        # an active licence's end date must not leak into the new trial's
        # _ends_date() / expired-ends computation after a reset
        ws = self._ws(state='active', licence_end=date.today() + timedelta(days=90))
        ws.action_reset_to_trial()
        self.assertEqual(ws.state, 'trial')
        self.assertFalse(ws.licence_end)
        self.assertEqual(ws._ends_date(), date.today() + timedelta(days=30))

    def test_form_view_renders_with_buttons(self):
        view = self.env.ref('techrise_workspace_license.view_techrise_workspace_form')
        arch = self.env['techrise.workspace'].get_view(view.id, 'form')['arch']
        for name in ('action_activate', 'action_block', 'action_reset_to_trial'):
            self.assertIn(name, arch)

    def test_search_view_has_state_filters(self):
        view = self.env.ref('techrise_workspace_license.view_techrise_workspace_search')
        arch = self.env['techrise.workspace'].get_view(view.id, 'search')['arch']
        for name in ('trial', 'active', 'expired', 'blocked'):
            self.assertIn('name="%s"' % name, arch)


from .common import SigningKeyMixin
from ..models.license_signer import WORKSPACE_PREFIX, _workspace_message


@tagged('post_install', '-at_install')
class TestWorkspaceSignature(SigningKeyMixin, TransactionCase):

    def test_message_format_is_canonical(self):
        msg = _workspace_message('abc', 'trial', '2026-10-18', 1758200000)
        self.assertEqual(msg, b'techrise-workspace:v1\nabc\ntrial\n2026-10-18\n1758200000')
        self.assertEqual(WORKSPACE_PREFIX, 'techrise-workspace:v1')

    def test_empty_ends_is_empty_line(self):
        msg = _workspace_message('abc', 'active', False, 1)
        self.assertEqual(msg, b'techrise-workspace:v1\nabc\nactive\n\n1')

    def test_workspace_signature_verifies(self):
        signer = self.env['techrise.license.signer']
        env = signer.workspace_signature('abc', 'trial', '2026-10-18')
        self.assertIn('iat', env)
        self.assertSigned(_workspace_message('abc', 'trial', '2026-10-18', env['iat']), env['sig'])

    def test_missing_key_returns_none(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'techrise_license.signing_key_path', '/nonexistent/key.pem')
        self.assertIsNone(self.env['techrise.license.signer'].workspace_signature('abc', 'trial', ''))
