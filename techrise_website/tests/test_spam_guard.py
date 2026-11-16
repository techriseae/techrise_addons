import re
import time

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.techrise_website.controllers.spam_guard import make_form_token, spam_reason


@tagged('post_install', '-at_install')
class TestSpamGuardHelpers(TransactionCase):

    def test_token_roundtrip(self):
        token = make_form_token(self.env, now=1000)
        self.assertIsNone(spam_reason(self.env, {'tr_ts': token}, now=1010))

    def test_too_fast(self):
        token = make_form_token(self.env, now=1000)
        self.assertEqual(spam_reason(self.env, {'tr_ts': token}, now=1001), 'too_fast')

    def test_old_form_ok(self):
        token = make_form_token(self.env, now=0)
        self.assertIsNone(spam_reason(self.env, {'tr_ts': token}, now=3 * 86400))

    def test_tampered_token(self):
        self.assertEqual(spam_reason(self.env, {'tr_ts': '1000.deadbeef'}, now=2000), 'bad_token')
        self.assertEqual(spam_reason(self.env, {}, now=2000), 'bad_token')
        self.assertEqual(spam_reason(self.env, {'tr_ts': 'garbage'}, now=2000), 'bad_token')

    def test_honeypot(self):
        token = make_form_token(self.env, now=1000)
        self.assertEqual(
            spam_reason(self.env, {'tr_ts': token, 'tr_hp_x9': 'x'}, now=1010), 'honeypot')


@tagged('post_install', '-at_install')
class TestContactRoute(HttpCase):

    def _form_page(self):
        res = self.url_open('/contactus')
        self.assertEqual(res.status_code, 200)
        return res.text

    def _post(self, **extra):
        html = self._form_page()
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        data = {
            'csrf_token': csrf,
            'name': 'Test Person',
            'email_from': 'test.person@example.com',
            'phone': '0501234567',
            'body': 'Real enquiry about Odoo',
            'tr_ts': make_form_token(self.env, now=time.time() - 10),
        }
        data.update(extra)
        return self.url_open('/contact/submit', data=data)

    def _lead_count(self):
        return self.env['crm.lead'].sudo().search_count([('email_from', '=', 'test.person@example.com')])

    def test_honeypot_markup(self):
        html = self._form_page()
        field = re.search(r'<input[^>]*name="tr_hp_x9"[^>]*>', html)
        self.assertTrue(field, 'honeypot field missing')
        self.assertIn('autocomplete="off"', field.group(0))
        self.assertIn('tabindex="-1"', field.group(0))
        self.assertRegex(html, r'name="tr_ts" value="\d+\.[0-9a-f]+"')

    def test_route_spam_creates_no_lead(self):
        before = self._lead_count()
        res = self._post(tr_hp_x9='spam')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._lead_count(), before)

    def test_route_real_creates_lead(self):
        before = self._lead_count()
        res = self._post()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._lead_count(), before + 1)


@tagged('post_install', '-at_install')
class TestTurnstile(TestContactRoute):

    def setUp(self):
        super().setUp()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('cf.turnstile_site_key', '1x00000000000000000000AA')
        icp.set_param('cf.turnstile_secret_key', '1x0000000000000000000000000000000AA')

    def _patch_result(self, result):
        IrHttp = type(self.env['ir.http'])
        self.patch(IrHttp, '_verify_turnstile_token', lambda self, ip, token, action=False: result)

    def test_widget_rendered_when_configured(self):
        html = self._form_page()
        self.assertTrue('data-sitekey="1x00000000000000000000AA"' in html, 'turnstile widget missing')
        self.assertTrue('data-response-field-name="turnstile_captcha"' in html, 'response field name missing')

    def test_turnstile_failure_blocks_lead(self):
        self._patch_result('wrong_token')
        before = self._lead_count()
        res = self._post(turnstile_captcha='bad')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._lead_count(), before)

    def test_turnstile_pass_creates_lead(self):
        self._patch_result('is_human')
        before = self._lead_count()
        self._post(turnstile_captcha='good')
        self.assertEqual(self._lead_count(), before + 1)


@tagged('post_install', '-at_install')
class TestTurnstileOff(TestContactRoute):

    def test_no_widget_without_site_key(self):
        self.env['ir.config_parameter'].sudo().set_param('cf.turnstile_site_key', False)
        self.assertFalse('cf-turnstile' in self._form_page(), 'widget rendered without site key')
