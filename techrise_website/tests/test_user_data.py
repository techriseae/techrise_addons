import hashlib
import re
import time

from odoo.tests import BaseCase, HttpCase, tagged

from odoo.addons.techrise_website.controllers.spam_guard import make_form_token
from odoo.addons.techrise_website.controllers.user_data import (
    hashed_user_data, normalize_email, normalize_phone_ae,
)


@tagged('post_install', '-at_install')
class TestNormalize(BaseCase):

    def test_uae_phone_formats(self):
        for raw in ('+971 50 123 4567', '0501234567', '00971501234567', '050-123-4567', '501234567', '971501234567'):
            self.assertEqual(normalize_phone_ae(raw), '+971501234567', raw)

    def test_foreign_phone_kept(self):
        self.assertEqual(normalize_phone_ae('+44 20 7946 0958'), '+442079460958')

    def test_bad_phone_dropped(self):
        for raw in ('12345', '', None, 'call me', '+12'):
            self.assertIsNone(normalize_phone_ae(raw), raw)

    def test_email(self):
        self.assertEqual(normalize_email('  Ali@Example.COM '), 'ali@example.com')
        self.assertIsNone(normalize_email('not-an-email'))
        self.assertIsNone(normalize_email(None))

    def test_hashes(self):
        data = hashed_user_data('a@b.co', '0501234567')
        self.assertEqual(data['ph'], hashlib.sha256(b'+971501234567').hexdigest())
        self.assertEqual(data['em'], hashlib.sha256(b'a@b.co').hexdigest())
        self.assertEqual(hashed_user_data('x', '1'), {'em': None, 'ph': None})


@tagged('post_install', '-at_install')
class TestThankYouUserData(HttpCase):

    def test_thankyou_has_hashes_not_plaintext(self):
        html = self.url_open('/contactus').text
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        res = self.url_open('/contact/submit', data={
            'csrf_token': csrf, 'name': 'Hash Test', 'email_from': 'Hash.Test@Example.com',
            'phone': '050 123 4567', 'body': 'hello',
            'tr_ts': make_form_token(self.env, now=time.time() - 10),
        })
        em = hashlib.sha256(b'hash.test@example.com').hexdigest()
        ph = hashlib.sha256(b'+971501234567').hexdigest()
        self.assertTrue(f'data-tr-ud-em="{em}"' in res.text, 'email hash missing')
        self.assertTrue(f'data-tr-ud-ph="{ph}"' in res.text, 'phone hash missing')
        self.assertFalse('hash.test@example.com' in res.text.lower(), 'plaintext email leaked')
