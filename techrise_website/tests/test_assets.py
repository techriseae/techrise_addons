import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestFrontendAssets(HttpCase):

    def test_frontend_css_compiles_with_site_styles(self):
        """A SCSS syntax error makes Odoo serve a bundle without our styles."""
        html = self.url_open('/').text
        href = re.search(r'href="(/web/assets/[^"]*web\.assets_frontend[^"]*\.css)"', html)
        self.assertTrue(href, 'frontend css bundle link missing')
        css = self.url_open(href.group(1)).text
        self.assertFalse('Invalid CSS' in css, 'SCSS compile error in web.assets_frontend')
        for selector in ('.tr-ai-console', '.tr-related-solutions', '.tr-hp'):
            self.assertTrue(selector in css, f'{selector} styles missing from compiled bundle')

    def _frontend_css(self):
        html = self.url_open('/').text
        href = re.search(r'href="(/web/assets/[^"]*web\.assets_frontend[^"]*\.css)"', html)
        return self.url_open(href.group(1)).text

    def test_fonts_are_self_hosted(self):
        """Google Fonts @import blocks rendering (~1.5 s on mobile PSI): serve Inter locally."""
        css = self._frontend_css()
        self.assertNotIn('fonts.googleapis.com', css)
        for name in ('inter-latin-wght-normal.woff2', 'inter-tight-latin-wght-normal.woff2'):
            url = f'/techrise_website/static/src/fonts/{name}'
            self.assertIn(url, css, f'@font-face for {name} missing')
            self.assertEqual(self.url_open(url).status_code, 200)


@tagged('post_install', '-at_install')
class TestSingleGtag(HttpCase):

    def test_odoo_native_gtag_not_loaded_twice(self):
        """Odoo's own eager gtag (website.google_analytics_key) doubled gtag.js and page_views;
        only our consent-aware lazy loader may load it."""
        self.env['website'].search([]).write({'google_analytics_key': 'G-TEST123'})
        html = self.url_open('/').text
        self.assertNotIn('id="tracking_code"', html)
        self.assertIn("gtag('config', 'G-CJTPLY088E'", html)
