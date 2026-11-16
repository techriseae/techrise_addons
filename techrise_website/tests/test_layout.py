import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCookieBar(HttpCase):

    def test_banner_contract(self):
        html = self.url_open('/').text
        for ident in ('tr-cookie-accept', 'tr-cookie-reject', 'tr-cookie-customize', 'tr-cookie-save'):
            self.assertTrue('id="%s"' % ident in html, ident)
        self.assertTrue('tr-cookie-bar' in html, 'compact bar class missing')
        # preferences stay hidden until "Customize"
        self.assertTrue(re.search(r'id="tr-cookie-preferences"[^>]*hidden', html), 'prefs not hidden')

    def test_banner_arabic_on_ar_pages(self):
        html = self.url_open('/ar').text
        self.assertTrue('نستخدم ملفات تعريف الارتباط' in html)

    def test_consent_default_still_denied(self):
        # Owner has not chosen regional defaults: keep denied-by-default, no region split.
        html = self.url_open('/').text
        self.assertTrue("'analytics_storage': 'denied'" in html)
        self.assertTrue("region" not in html.split("gtag('consent', 'default'")[1].split('</script>')[0])
