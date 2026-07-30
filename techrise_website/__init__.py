from . import controllers
from . import models


def _unpublish_all_jobs(env):
    """Ensure all hr.job records are unpublished. Career pages are disabled."""
    jobs = env['hr.job'].sudo().search([('is_published', '=', True)])
    if jobs:
        jobs.write({'is_published': False})


def _post_init_hook(env):
    """Fix menu parent IDs to point to the website-specific top menu."""
    _unpublish_all_jobs(env)
    env['website']._tr_apply_menu_cleanup()