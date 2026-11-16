"""Sync website-specific copies of the homepage with the new design.

On techriseae.com the homepage view was saved once from the website editor,
which created website-specific copies (COW) of ``techrise_homepage``. Odoo
does not update edited copies on module upgrade, so the live site kept the
old hero. Those copies only contained editor noise (canvas tags, filled
counters, re-escaped ampersands), so they are reset to the module's arch.
"""
import logging

_logger = logging.getLogger(__name__)

_KEYS = ('techrise_website.techrise_homepage', 'techrise_website.homepage_seo')


def migrate(cr, version):
    for key in _KEYS:
        cr.execute("""
            UPDATE ir_ui_view s
               SET arch_db = g.arch_db, write_date = now() at time zone 'UTC'
              FROM ir_ui_view g
             WHERE s.key = %s AND s.website_id IS NOT NULL
               AND g.key = s.key AND g.website_id IS NULL
               AND s.arch_db IS DISTINCT FROM g.arch_db
         RETURNING s.id, s.website_id
        """, (key,))
        for view_id, website_id in cr.fetchall():
            _logger.info("techrise_website: reset %s copy %s (website %s) to module arch", key, view_id, website_id)
