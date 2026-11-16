import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, arabic_ratio, main_text, parse


@tagged('post_install', '-at_install')
class TestRetailPage(HttpCase):

    def _words(self, doc):
        return len(main_text(doc).split())

    def test_english_depth(self):
        doc = parse(fetch(self, '/erp-for-retail-uae').text)
        self.assertGreaterEqual(self._words(doc), 1200, 'EN word count')
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, 'h2 count')
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'FAQ items')
        hrefs = set(doc.xpath('//main//a/@href'))
        for link in ('/inventory-procurement-uae', '/accounting-software-uae', '/contactus'):
            self.assertIn(link, hrefs, 'missing internal link %s' % link)

    def test_arabic_depth(self):
        doc = parse(fetch(self, '/ar/erp-for-retail-uae').text)
        self.assertGreaterEqual(self._words(doc), 900, 'AR word count')
        self.assertGreaterEqual(arabic_ratio(doc), 0.7, 'AR ratio')
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'AR FAQ items')
