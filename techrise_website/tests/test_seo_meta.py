import re

from odoo.tests import HttpCase, tagged

from ._pages import fetch, parse, sitemap_paths, title_and_desc


@tagged('post_install', '-at_install')
class TestSeoMeta(HttpCase):

    def test_titles_and_descriptions(self):
        paths = sitemap_paths(self)
        self.assertEqual(len(paths), 36, 'sitemap should list 36 pages')
        titles, descs, bad = {}, {}, []
        for path in paths:
            doc = parse(fetch(self, path).text)
            title, desc = title_and_desc(doc)
            if len(title) > 60:
                bad.append('%s title %d' % (path, len(title)))
            if not 120 <= len(desc) <= 155:
                bad.append('%s desc %d' % (path, len(desc)))
            if title in titles:
                bad.append('%s duplicate title with %s' % (path, titles[title]))
            if desc in descs:
                bad.append('%s duplicate description with %s' % (path, descs[desc]))
            titles[title] = path
            descs[desc] = path
        self.assertFalse(bad, 'SEO meta problems: %s' % '; '.join(bad))

    def test_homepage_keeps_keywords(self):
        for path, needles in (('/', ('Odoo Partner', 'Abu Dhabi')), ('/ar', ('شريك Odoo', 'أبوظبي'))):
            title, _desc = title_and_desc(parse(fetch(self, path).text))
            for needle in needles:
                self.assertIn(needle, title, '%s title lacks %s' % (path, needle))


@tagged('post_install', '-at_install')
class TestHomepageMetaOverrides(HttpCase):

    def test_homepage_uses_new_title(self):
        """Backend SEO titles saved on website.homepage must not override the template title."""
        html = self.url_open('/').text
        title = re.search(r'<title>(.*?)</title>', html, re.S).group(1)
        self.assertTrue('Odoo Partner Abu Dhabi' in title, f'old homepage title still served: {title}')
