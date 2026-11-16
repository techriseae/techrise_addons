from odoo.tests import HttpCase, tagged

from ._pages import fetch, AR_RE, arabic_ratio, parse, sitemap_paths, title_and_desc


@tagged('post_install', '-at_install')
class TestArabicPages(HttpCase):

    def test_every_ar_page_is_arabic(self):
        paths = [p for p in sitemap_paths(self) if p == '/ar' or p.startswith('/ar/')]
        self.assertTrue(len(paths) >= 17, 'expected the Arabic sitemap entries')
        bad = []
        for path in paths:
            res = fetch(self, path)
            self.assertEqual(res.status_code, 200, path)
            doc = parse(res.text)
            ratio = arabic_ratio(doc, drop_hero=(path in ('/ar', '/ar/')))
            h1 = doc.xpath('//h1')
            h1_text = ''.join(h1[0].itertext()) if h1 else ''
            title, desc = title_and_desc(doc)
            if ratio < 0.7:
                bad.append('%s ratio=%.2f' % (path, ratio))
            # the homepage H1 belongs to the hero, owned by another task
            if path not in ('/ar', '/ar/') and not AR_RE.search(h1_text):
                bad.append('%s h1 not Arabic' % path)
            if not AR_RE.search(title):
                bad.append('%s title not Arabic' % path)
            if not AR_RE.search(desc):
                bad.append('%s description not Arabic' % path)
        self.assertFalse(bad, 'Arabic gaps: %s' % '; '.join(bad))
