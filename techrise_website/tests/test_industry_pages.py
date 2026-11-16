import json
import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, arabic_ratio, main_text, parse

PAGES = {
    'construction': ('/erp-for-construction-uae', '/ar/erp-for-construction-uae',
                     ('/inventory-procurement-uae', '/hr-payroll-software-uae',
                      '/accounting-software-uae', '/contactus')),
    'healthcare': ('/erp-for-healthcare-uae', '/ar/erp-for-healthcare-uae',
                   ('/accounting-software-uae', '/hr-payroll-software-uae',
                    '/call-center-software-uae', '/contactus')),
}


@tagged('post_install', '-at_install')
class TestIndustryPages(HttpCase):

    def _check_en(self, key):
        en, _ar, links = PAGES[key]
        text = fetch(self, en).text
        doc = parse(text)
        self.assertGreaterEqual(len(main_text(doc).split()), 1200, '%s EN words' % key)
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, '%s h2' % key)
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, '%s FAQ' % key)
        hrefs = set(doc.xpath('//main//a/@href'))
        for link in links:
            self.assertIn(link, hrefs, '%s missing link %s' % (key, link))
        # internal links stand alone in their own paragraph
        for link in links[:-1]:
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
        self.assertGreaterEqual(len(main_text(doc).split()), 900, '%s AR words' % key)
        self.assertGreaterEqual(arabic_ratio(doc), 0.7, '%s AR ratio' % key)
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, '%s AR FAQ' % key)
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, '%s AR h2' % key)

    def test_construction_en(self):
        self._check_en('construction')

    def test_construction_ar(self):
        self._check_ar('construction')

    def test_healthcare_en(self):
        self._check_en('healthcare')

    def test_healthcare_ar(self):
        self._check_ar('healthcare')
