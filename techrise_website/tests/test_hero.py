import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestHomepageHero(HttpCase):

    def _h1(self, html):
        m = re.search(r'<h1[^>]*id="tr-hero-title"[^>]*>(.*?)</h1>', html, re.S)
        self.assertTrue(m, 'hero h1 missing')
        return ' '.join(re.sub(r'<[^>]+>', ' ', m.group(1)).split())

    def test_en_hero(self):
        html = self.url_open('/').text
        h1 = self._h1(html)
        for word in ('AI-powered', 'Odoo Partner', 'Abu Dhabi'):
            self.assertIn(word, h1)
        self.assertTrue('class="tr-hero tr-hero--ai"' in html, 'ai hero class missing')
        self.assertTrue('class="tr-ai-console"' in html, 'console missing')
        # first demo server-rendered (no-JS / crawler visible)
        self.assertTrue('Which invoices are overdue more than 30 days?' in html, 'first demo question')
        self.assertTrue('Gulf Build LLC' in html, 'first demo rows')
        self.assertTrue('data-tr-event="consultation_cta_click"' in html, 'primary CTA event')
        self.assertTrue('tr-hero-confetti' not in html, 'confetti still present')
        self.assertTrue('https://www.odoo.com/partners?search=techrise' in html, 'partner badge link')

    def test_ar_hero(self):
        html = self.url_open('/ar').text
        h1 = self._h1(html)
        self.assertIn('شريك Odoo', h1)
        self.assertIn('أبوظبي', h1)
        self.assertTrue('إيه الفواتير المتأخرة أكتر من 30 يوم؟' in html, 'ar first demo question')
        self.assertTrue('Which invoices are overdue' not in html, 'english demo leaked into /ar')

    def test_old_hero_scripts_removed(self):
        html = self.url_open('/').text
        bundles = re.findall(r'src="(/web/assets/[^"]+\.js)"', html)
        self.assertTrue(bundles, 'no js bundle found')
        for url in bundles:
            js = self.url_open(url).text
            for name in ('tr_hero_bg', 'tr_decode_text', 'tr_splash_cursor'):
                self.assertTrue(name not in js, '%s still bundled' % name)
        self.assertTrue('tr-splash-cursor' not in html and 'tr-hero-bg' not in html)

    def test_critical_css_has_hero_h1(self):
        html = self.url_open('/').text
        self.assertTrue(re.search(r'<style>[^<]*\.tr-hero--ai[^<]*#tr-hero-title|<style>[^<]*\.tr-hero--ai h1', html),
                        'inline critical css for hero h1 missing')
