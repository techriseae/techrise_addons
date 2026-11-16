import json
import re

from odoo.tests import HttpCase, tagged

PRODUCT_PATHS = [
    '/accounting-software-uae', '/hr-payroll-software-uae',
    '/call-center-software-uae', '/inventory-procurement-uae',
    '/erp-software-uae', '/custom-software-uae',
]
INDUSTRY_PATHS = [
    '/erp-for-construction-uae', '/erp-for-healthcare-uae', '/erp-for-retail-uae',
    '/odoo-partner-abu-dhabi', '/odoo-partner-dubai',
]
SERVICE_PATHS = PRODUCT_PATHS + INDUSTRY_PATHS + ['/erp-suite']
OTHER_PATHS = ['/about', '/services', '/server', '/contactus',
               '/privacy-policy', '/terms-and-conditions']

LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
FAQ_RE = re.compile(
    r'<details class="tr-faq[^"]*">\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>', re.S)
TAG_RE = re.compile(r'<[^>]+>')


def _norm(text):
    import html
    return ' '.join(html.unescape(TAG_RE.sub('', text)).split())


@tagged('post_install', '-at_install')
class TestSchema(HttpCase):

    def _blocks(self, path):
        res = self.url_open(path)
        self.assertEqual(res.status_code, 200, path)
        blocks = []
        for raw in LD_RE.findall(res.text):
            blocks.append(json.loads(raw))  # must parse
        return res.text, blocks

    def _types(self, blocks):
        return [b.get('@type') for b in blocks]

    def test_all_blocks_parse_everywhere(self):
        for path in ['/', '/ar'] + SERVICE_PATHS + OTHER_PATHS:
            self._blocks(path)

    def test_service_pages_have_service_and_breadcrumb(self):
        for prefix in ('', '/ar'):
            for path in SERVICE_PATHS:
                _html, blocks = self._blocks(prefix + path)
                types = self._types(blocks)
                self.assertIn('Service', types, prefix + path)
                self.assertIn('BreadcrumbList', types, prefix + path)
                svc = next(b for b in blocks if b['@type'] == 'Service')
                self.assertEqual(svc['provider'], {'@id': 'https://techriseae.com/#organization'})
                self.assertEqual(svc['areaServed']['name'], 'United Arab Emirates')
                bc = next(b for b in blocks if b['@type'] == 'BreadcrumbList')
                self.assertEqual(len(bc['itemListElement']), 2)
                self.assertTrue(bc['itemListElement'][1]['item'].endswith(prefix + path))

    def test_other_pages_have_breadcrumb(self):
        for path in OTHER_PATHS:
            _html, blocks = self._blocks(path)
            self.assertIn('BreadcrumbList', self._types(blocks), path)
            self.assertNotIn('Service', self._types(blocks), path)

    def test_home_has_no_breadcrumb(self):
        _html, blocks = self._blocks('/')
        self.assertNotIn('BreadcrumbList', self._types(blocks))
        self.assertIn('Organization', self._types(blocks))

    def test_arabic_breadcrumb_is_arabic(self):
        _html, blocks = self._blocks('/ar/accounting-software-uae')
        bc = next(b for b in blocks if b['@type'] == 'BreadcrumbList')
        for el in bc['itemListElement']:
            self.assertTrue(re.search('[؀-ۿ]', el['name']), el['name'])
        _html, blocks = self._blocks('/ar/about')
        bc = next(b for b in blocks if b['@type'] == 'BreadcrumbList')
        self.assertTrue(re.search('[؀-ۿ]', bc['itemListElement'][1]['name']))

    def test_faqpage_matches_visible_faq(self):
        with_faq = 0
        for prefix in ('', '/ar'):
            for path in SERVICE_PATHS:
                html, blocks = self._blocks(prefix + path)
                visible = [(_norm(q), _norm(a)) for q, a in FAQ_RE.findall(html)]
                faq = [b for b in blocks if b['@type'] == 'FAQPage']
                if not visible:
                    self.assertFalse(faq, 'FAQPage without visible FAQ: ' + prefix + path)
                    continue
                with_faq += 1
                self.assertEqual(len(faq), 1, prefix + path)
                got = [(_norm(e['name']), _norm(e['acceptedAnswer']['text']))
                       for e in faq[0]['mainEntity']]
                self.assertEqual(got, visible, 'FAQ mismatch on ' + prefix + path)
        self.assertTrue(with_faq >= 4, 'expected FAQ on the product pages')

    def test_helper_faq_and_escaping(self):
        website = self.env['website'].browse(1)
        data = website._tr_service_jsonld(
            'Svc </script><b>', 'Desc', [('Q1?', 'A1 </script>')],
            'https://techriseae.com/x', 'Home')
        types = [d['@type'] for d in data]
        self.assertEqual(types, ['Service', 'BreadcrumbList', 'FAQPage'])
        out = str(website._tr_jsonld(data[0]))
        self.assertNotIn('</', out)
        self.assertEqual(json.loads(out)['name'], 'Svc </script><b>')
        no_faq = website._tr_service_jsonld('S', 'D', None, 'https://techriseae.com/x', 'Home')
        self.assertEqual([d['@type'] for d in no_faq], ['Service', 'BreadcrumbList'])

    def test_website_searchaction_only_if_search_works(self):
        html, blocks = self._blocks('/')
        site = next(b for b in blocks if b['@type'] == 'WebSite')
        if 'potentialAction' in site:
            res = self.url_open('/website/search?search=odoo')
            self.assertEqual(res.status_code, 200)
