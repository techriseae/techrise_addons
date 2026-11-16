import json
import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, arabic_ratio, main_text, parse

COMMON = ('/accounting-software-uae', '/hr-payroll-software-uae', '/erp-software-uae', '/contactus')
PAGES = {
    'abu_dhabi': ('/odoo-partner-abu-dhabi', '/ar/odoo-partner-abu-dhabi',
                  COMMON + ('/odoo-partner-dubai',),
                  'Odoo Partner in Abu Dhabi', 'شريك Odoo في أبوظبي'),
    'dubai': ('/odoo-partner-dubai', '/ar/odoo-partner-dubai',
              COMMON + ('/odoo-partner-abu-dhabi',),
              'Odoo Partner in Dubai', 'شريك Odoo في دبي'),
}
PARTNER_URL = 'https://www.odoo.com/partners?search=techrise'


@tagged('post_install', '-at_install')
class TestCityPages(HttpCase):

    def _check_en(self, key):
        en, _ar, links, h1_en, _h1_ar = PAGES[key]
        text = fetch(self, en).text
        doc = parse(text)
        h1 = ' '.join(''.join(doc.xpath('//main//h1')[0].itertext()).split())
        self.assertIn(h1_en, h1, '%s H1' % key)
        self.assertGreaterEqual(len(main_text(doc).split()), 1200, '%s EN words' % key)
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, '%s h2' % key)
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, '%s FAQ' % key)
        hrefs = set(doc.xpath('//main//a/@href'))
        self.assertIn(PARTNER_URL, hrefs, '%s partner link' % key)
        for link in links:
            self.assertIn(link, hrefs, '%s missing link %s' % (key, link))
        for link in links[:-2] + links[-1:]:
            if link == '/contactus':
                continue
            own = doc.xpath('//main//p[a[@href="%s"]]' % link)
            self.assertTrue(own and all(len(p.xpath('./a')) == 1 and not (p.text or '').strip() for p in own),
                            '%s link %s not on its own line' % (key, link))
        types = {}
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            data = json.loads(raw)
            for item in (data if isinstance(data, list) else [data]):
                types[item.get('@type')] = item
        self.assertIn('FAQPage', types, '%s FAQPage JSON-LD' % key)
        self.assertEqual(len(types['FAQPage']['mainEntity']), 6, '%s FAQ JSON-LD items' % key)

    def _check_ar(self, key):
        doc = parse(fetch(self, PAGES[key][1]).text)
        h1 = ' '.join(''.join(doc.xpath('//main//h1')[0].itertext()).split())
        self.assertIn(PAGES[key][4], h1, '%s AR H1' % key)
        self.assertGreaterEqual(len(main_text(doc).split()), 900, '%s AR words' % key)
        self.assertGreaterEqual(arabic_ratio(doc), 0.7, '%s AR ratio' % key)
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, '%s AR FAQ' % key)
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, '%s AR h2' % key)

    def test_abu_dhabi_en(self):
        self._check_en('abu_dhabi')

    def test_abu_dhabi_ar(self):
        self._check_ar('abu_dhabi')

    def test_dubai_en(self):
        self._check_en('dubai')

    def test_dubai_ar(self):
        self._check_ar('dubai')

    def test_pages_not_near_duplicates(self):
        a = set(main_text(parse(fetch(self, PAGES['abu_dhabi'][0]).text)).lower().split())
        d = set(main_text(parse(fetch(self, PAGES['dubai'][0]).text)).lower().split())
        self.assertTrue(len(a & d) / len(a | d) < 0.6, 'pages share too much vocabulary')
