import json
import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, arabic_ratio, main_text, parse, title_and_desc

EN = '/hr-payroll-software-uae'
AR = '/ar/hr-payroll-software-uae'
LINKS = ('/accounting-software-uae', '/erp-software-uae', '/odoo-partner-abu-dhabi', '/contactus')


@tagged('post_install', '-at_install')
class TestPayrollPage(HttpCase):

    def test_payroll_en(self):
        text = fetch(self, EN).text
        doc = parse(text)
        body = main_text(doc)
        self.assertGreaterEqual(len(body.split()), 1200, 'EN words')
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, 'h2')
        h1 = ' '.join(''.join(doc.xpath('//main//h1')[0].itertext()).split())
        self.assertIn('WPS', h1, 'H1 has WPS')
        for term in ('SIF', 'EDR', 'EVP', 'SCR', 'MOHRE'):
            self.assertIn(term, body, 'mentions %s' % term)
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'FAQ')
        hrefs = set(doc.xpath('//main//a/@href'))
        for link in LINKS:
            self.assertIn(link, hrefs, 'missing link %s' % link)
            own = doc.xpath('//main//p[a[@href="%s"]]' % link)
            self.assertTrue(own and all(len(p.xpath('./a')) == 1 and not (p.text or '').strip() for p in own),
                            'link %s not on its own line' % link)
        title, desc = title_and_desc(doc)
        self.assertTrue(title.lower().startswith('wps payroll software uae'), 'title leads with WPS: %s' % title)
        self.assertLessEqual(len(title), 60, 'title length')
        self.assertTrue(120 <= len(desc) <= 155, 'desc length %s' % len(desc))
        self.assertTrue(desc.lower().startswith('wps payroll software uae'), 'desc leads with WPS')
        types = {}
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            data = json.loads(raw)
            for item in (data if isinstance(data, list) else [data]):
                types[item.get('@type')] = item
        self.assertIn('FAQPage', types, 'FAQPage JSON-LD')
        self.assertEqual(len(types['FAQPage']['mainEntity']), 6, 'FAQ JSON-LD items')

    def test_payroll_ar(self):
        doc = parse(fetch(self, AR).text)
        self.assertGreaterEqual(len(main_text(doc).split()), 900, 'AR words')
        self.assertGreaterEqual(arabic_ratio(doc), 0.7, 'AR ratio')
        self.assertEqual(len(doc.xpath('//main//details[contains(@class, "tr-faq")]/summary')), 6, 'AR FAQ')
        self.assertGreaterEqual(len(doc.xpath('//main//h2')), 6, 'AR h2')
        h1 = ' '.join(''.join(doc.xpath('//main//h1')[0].itertext()).split())
        self.assertIn('WPS', h1, 'AR H1 has WPS')
        self.assertTrue(re.search(r'[؀-ۿ]', h1), 'AR H1 is Arabic')
        title, desc = title_and_desc(doc)
        self.assertLessEqual(len(title), 60, 'AR title length')
        self.assertTrue(120 <= len(desc) <= 155, 'AR desc length %s' % len(desc))
        self.assertIn('WPS', title, 'AR title has WPS')
