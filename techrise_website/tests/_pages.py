import re
from urllib.parse import urlparse

from lxml import html as lxml_html

AR_RE = re.compile(r'[؀-ۿ]')
LATIN_RE = re.compile(r'[A-Za-z]+')
BRAND_WORDS = {'odoo', 'techrise', 'wps', 'vat', 'erp', 'crm', 'pos', 'api'}


def sitemap_paths(case):
    res = fetch(case, '/sitemap.xml')
    locs = re.findall(r'<loc>([^<]*)</loc>', res.text)
    paths = []
    for loc in locs:
        p = urlparse(loc).path or '/'
        if p not in paths:
            paths.append(p)
    return paths


def fetch(case, path):
    """GET without carrying the language cookie from earlier requests."""
    case.opener.cookies.clear()
    return case.url_open(path)


def parse(text):
    return lxml_html.fromstring(text)


def main_text(doc, drop_hero=False):
    mains = doc.xpath('//main')
    main = mains[0] if mains else doc
    for el in main.xpath('.//script|.//style'):
        el.getparent().remove(el)
    if drop_hero:
        for el in main.xpath('.//section[contains(concat(" ", normalize-space(@class), " "), " tr-hero")]'):
            el.getparent().remove(el)
    return ' '.join(main.itertext())


def arabic_ratio(doc, drop_hero=False):
    text = main_text(doc, drop_hero)
    text = LATIN_RE.sub(lambda m: '' if m.group(0).lower() in BRAND_WORDS else m.group(0), text)
    ar = len(AR_RE.findall(text))
    la = len(re.findall(r'[A-Za-z]', text))
    return ar / max(ar + la, 1)


def title_and_desc(doc):
    title = (doc.findtext('.//title') or '').strip()
    desc = (doc.xpath('//meta[@name="description"]/@content') or [''])[0].strip()
    return title, desc
