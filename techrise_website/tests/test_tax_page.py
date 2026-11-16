import json
import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, arabic_ratio, main_text, parse

EN = '/corporate-tax-odoo-uae'
AR = '/ar/corporate-tax-odoo-uae'
# /odoo-partner-abu-dhabi is built on another branch; it may 404 here.
LINKS = ('/accounting-software-uae', '/erp-software-uae', '/odoo-partner-abu-dhabi', '/contactus')
RESOLVING = ('/accounting-software-uae', '/erp-software-uae', '/contactus')


@tagged('post_install', '-at_install')
class TestTaxPage(HttpCase):

    def test_en(self):
        text = fetch(self, EN).text
        doc = parse(text)
        self.assertGreaterEqual(len(main_text(doc).split()), 1200, 'EN words')
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, 'h2')
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'FAQ')
        h1 = ' '.join(doc.xpath('//main//h1')[0].itertext())
        self.assertIn('UAE Corporate Tax', h1)
        self.assertIn('Odoo', h1)
        body = main_text(doc)
        self.assertIn('375,000', body)
        self.assertIn('9%', body)
        hrefs = set(doc.xpath('//main//a/@href'))
        for link in LINKS:
            self.assertIn(link, hrefs, 'missing link %s' % link)
            own = doc.xpath('//main//p[a[@href="%s"]]' % link)
            self.assertTrue(own and all(len(p.xpath('./a')) == 1 and not (p.text or '').strip() for p in own),
                            'link %s not on its own line' % link)
        for link in RESOLVING:
            self.assertEqual(self.url_open(link).status_code, 200, link)
        types = {}
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            data = json.loads(raw)
            for item in (data if isinstance(data, list) else [data]):
                types[item.get('@type')] = item
        self.assertIn('FAQPage', types)
        self.assertEqual(len(types['FAQPage']['mainEntity']), 6)

    def test_ar(self):
        doc = parse(fetch(self, AR).text)
        self.assertGreaterEqual(len(main_text(doc).split()), 900, 'AR words')
        self.assertGreaterEqual(arabic_ratio(doc), 0.7, 'AR ratio')
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'AR FAQ')
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, 'AR h2')
        h1 = ' '.join(doc.xpath('//main//h1')[0].itertext())
        self.assertIn('ضريبة الشركات', h1)
        self.assertIn('Odoo', h1)
        body = main_text(doc)
        self.assertIn('375,000', body)
        self.assertIn('9', body)
