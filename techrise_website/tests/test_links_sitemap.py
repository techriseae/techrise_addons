import re
from collections import Counter

from odoo.tests import HttpCase, tagged

PRODUCT_PATHS = [
    '/accounting-software-uae', '/hr-payroll-software-uae',
    '/call-center-software-uae', '/inventory-procurement-uae',
    '/erp-software-uae', '/custom-software-uae',
]
INDUSTRY_PATHS = [
    '/erp-for-construction-uae', '/erp-for-healthcare-uae', '/erp-for-retail-uae',
]
SOLUTIONS = PRODUCT_PATHS + INDUSTRY_PATHS

MAIN_RE = re.compile(r'<main\b.*?</main>', re.S)
HREF_RE = re.compile(r'href="([^"#?]*)')


def _hrefs(html, only_main=False):
    if only_main:
        m = MAIN_RE.search(html)
        html = m.group(0) if m else ''
    return {h.rstrip('/') or '/' for h in HREF_RE.findall(html)}


@tagged('post_install', '-at_install')
class TestLinksSitemap(HttpCase):

    def _sitemap(self):
        self.env['ir.attachment'].sudo().search(
            [('url', '=like', '/sitemap-%')]).unlink()
        res = self.url_open('/sitemap.xml')
        self.assertEqual(res.status_code, 200)
        return res.text

    def test_footer_links_all_solutions(self):
        for prefix in ('', '/ar'):
            res = self.url_open(prefix or '/')
            m = re.search(r'<footer.*?</footer>|<div id="footer".*', res.text, re.S)
            hrefs = _hrefs(m.group(0))
            for path in SOLUTIONS + ['/erp-suite', '/server']:
                self.assertIn(prefix + path, hrefs, 'footer missing ' + prefix + path)

    def test_each_solution_has_inlinks(self):
        locs = re.findall(r'<loc>https?://[^/<]+(/[^<]*)</loc>', self._sitemap())
        pages = [p for p in locs if not p.startswith('/ar')]
        counts = Counter()
        for page in pages:
            res = self.url_open(page)
            if res.status_code != 200:
                continue
            for h in _hrefs(res.text, only_main=True):
                if h in SOLUTIONS and h != page:
                    counts[h] += 1
        for path in SOLUTIONS:
            self.assertTrue(counts[path] >= 3, '%s has %d inlinks' % (path, counts[path]))

    def test_sitemap_lastmod(self):
        xml = self._sitemap()
        urls = re.findall(r'<url>(.*?)</url>', xml, re.S)
        self.assertTrue(urls)
        for block in urls:
            self.assertTrue(
                re.search(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>', block),
                'no lastmod: ' + block.strip()[:120])
