import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestTrustedBy(HttpCase):

    def _section(self, path):
        html = self.url_open(path).text
        m = re.search(r'<section[^>]*id="clients"[^>]*>(.*?)</section>', html, re.S)
        self.assertTrue(m, f'clients section missing on {path}')
        return m.group(1)

    def test_three_client_stories(self):
        sec = self._section('/')
        self.assertEqual(len(re.findall(r'<article class="tr-case"', sec)), 3, 'expected 3 client stories')
        for name in ('South Westman', 'Nova International', 'Global Hair Dubai'):
            self.assertTrue(name in sec, f'{name} story missing')
        for logo in ('swm.webp', 'nova.webp', 'globalhair.webp'):
            self.assertTrue(logo in sec, f'{logo} missing')

    def test_strip_only_real_logos(self):
        sec = self._section('/')
        for logo in ('norm.webp', 'alyafour.svg', 'venezia.webp'):
            self.assertTrue(logo in sec, f'{logo} missing from strip')
        for placeholder in ('gulf.svg', 'goldenbest.svg', 'lifemarketing.svg', 'lotfytravel.svg', 'nof.svg', 'aldalil'):
            self.assertFalse(placeholder in sec, f'{placeholder} must not be shown')

    def test_old_selector_removed(self):
        sec = self._section('/')
        self.assertFalse('tr-clientsel' in sec, 'old interactive chips still rendered')

    def test_arabic_stories(self):
        sec = self._section('/ar')
        self.assertEqual(len(re.findall(r'<article class="tr-case"', sec)), 3, 'expected 3 stories on /ar')
        self.assertTrue('موثوق' in sec or 'يثق' in sec, 'Arabic section title missing')
        self.assertTrue('الرواتب' in sec, 'Arabic story text missing')
