"""Bot protection for the public contact form.

Two cheap server-side checks that need no third-party service:

* a honeypot field (``tr_hp_x9``) that humans never see or fill;
* a signed render timestamp (``tr_ts``): bots that post instantly, or post
  without loading the page, are rejected. Old forms are fine — only
  submissions faster than ``MIN_FILL_SECONDS`` count as spam.
"""
import hmac as _hmac
import time

from odoo.tools.misc import hmac

HONEYPOT_FIELD = 'tr_hp_x9'
TOKEN_FIELD = 'tr_ts'
MIN_FILL_SECONDS = 3
_SCOPE = 'tr-contact-form'


def make_form_token(env, now=None):
    ts = int(time.time() if now is None else now)
    return f"{ts}.{hmac(env(su=True), _SCOPE, str(ts))}"


def spam_reason(env, params, now=None):
    """Return why ``params`` looks like spam, or ``None`` for a real submit."""
    if (params.get(HONEYPOT_FIELD) or '').strip():
        return 'honeypot'
    ts_str, _, sig = (params.get(TOKEN_FIELD) or '').partition('.')
    if not ts_str.isdigit() or not sig:
        return 'bad_token'
    expected = hmac(env(su=True), _SCOPE, ts_str)
    if not _hmac.compare_digest(expected, sig):
        return 'bad_token'
    now = time.time() if now is None else now
    if now - int(ts_str) < MIN_FILL_SECONDS:
        return 'too_fast'
    return None
