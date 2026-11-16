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
