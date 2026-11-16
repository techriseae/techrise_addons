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


@tagged('post_install', '-at_install')
class TestHeadingOrder(HttpCase):

    def test_footer_titles_do_not_skip_heading_levels(self):
        """Lighthouse heading-order: footer column titles were <h5> right after page <h3>s."""
        html = self.url_open('/').text
        footer = html.split('id="footer"', 1)[1]
        self.assertNotIn('<h5', footer.split('id="tr-cookie-banner"')[0])
        self.assertIn('<h2 class="tr-footer-h">Quick Links</h2>', footer)


@tagged('post_install', '-at_install')
class TestFooterNewPages(HttpCase):

    def test_footer_links_new_seo_pages(self):
        """Every page links to the city and tax pages (internal links for ranking)."""
        footer = self.url_open('/').text.split('id="footer"', 1)[1]
        for href, label in (('/corporate-tax-odoo-uae', 'Corporate Tax in Odoo'),
                            ('/odoo-partner-abu-dhabi', 'Odoo Partner Abu Dhabi'),
                            ('/odoo-partner-dubai', 'Odoo Partner Dubai')):
            self.assertIn('<a href="%s">%s</a>' % (href, label), footer)
        self.opener.cookies.clear()
        ar_footer = self.url_open('/ar').text.split('id="footer"', 1)[1]
        self.assertIn('شريك Odoo في أبوظبي</a>', ar_footer)
        self.assertIn('ضريبة الشركات في Odoo</a>', ar_footer)
