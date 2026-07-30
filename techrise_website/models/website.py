from odoo import api, models


# URLs intentionally excluded from the public sitemap.
# - /contact     : 301 alias of canonical /contactus
# - /jobs*       : career pages are intentionally unpublished
# - /website/info: Odoo introspection page, not meant for public SEO
_SITEMAP_EXCLUDED_PREFIXES = ('/contact', '/jobs', '/website/info')
_SITEMAP_EXCLUDED_EXACT = {'/contact'}


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _tr_apply_menu_cleanup(self):
        """Re-parent every Techrise top-level menu to the website's real top
        menu, drop duplicate default menus and career links. Safe to run on
        every module update (idempotent)."""
        env = self.env
        website = env.ref('website.default_website', raise_if_not_found=False)
        if not website:
            return
        # Branding — overrides the default "My Website" / "My Company"
        # placeholders (their data records are noupdate, so set them here).
        if website.name != 'Techrise':
            website.name = 'Techrise'
        company = website.company_id or env.company
        if company and company.name != 'Techrise':
            company.name = 'Techrise'
        if company and not company.phone:
            company.phone = '+971 58 595 5064'
        top_menu = env['website.menu'].search([
            ('website_id', '=', website.id),
            ('parent_id', '=', False),
        ], limit=1)
        if not top_menu:
            return
        menu_xmlids = [
            'techrise_website.menu_home',
            'techrise_website.menu_about',
            'techrise_website.menu_services',
            'techrise_website.menu_suite',
            'techrise_website.menu_solutions',
            'techrise_website.menu_industries',
            'techrise_website.menu_contact',
        ]
        kept_ids = []
        for xmlid in menu_xmlids:
            menu = env.ref(xmlid, raise_if_not_found=False)
            if menu:
                kept_ids.append(menu.id)
                if menu.parent_id != top_menu:
                    menu.parent_id = top_menu
        # Remove duplicate default Home / Contact items that sit next to ours.
        dups = env['website.menu'].search([
            ('parent_id', '=', top_menu.id),
            ('url', 'in', ['/', '/contactus', '/contact']),
            ('id', 'not in', kept_ids),
        ])
        dups.unlink()
        # Careers pages are disabled — drop any stray Jobs menu item.
        env['website.menu'].search([
            '|', ('url', '=like', '/jobs%'), ('name', 'ilike', 'job'),
        ]).unlink()

    def _enumerate_pages(self, query_string=None, force=False):
        """Filter out duplicate/unwanted URLs from the sitemap."""
        seen = set()
        for page in super()._enumerate_pages(query_string=query_string, force=force):
            url = (page.get('loc') or '').rstrip('/') or '/'
            if url in _SITEMAP_EXCLUDED_EXACT:
                continue
            if any(url == p or url.startswith(p + '/') for p in _SITEMAP_EXCLUDED_PREFIXES):
                continue
            if url in seen:
                continue
            seen.add(url)
            yield page