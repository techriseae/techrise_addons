"""Google Ads Enhanced Conversions: normalized + SHA-256 hashed user data.

Only hashes leave the server; the thank-you page hands them to
``gtag('set', 'user_data', ...)`` right before the conversion event.
"""
import hashlib
import re

_UAE_MOBILE = re.compile(r'^5\d{8}$')


def normalize_email(raw):
    email = (raw or '').strip().lower()
    return email if re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) else None


def normalize_phone_ae(raw):
    """E.164 for UAE numbers typed in local formats; None when unsure."""
    s = re.sub(r'[\s\-().]', '', raw or '')
    if s.startswith('00'):
        s = '+' + s[2:]
    if s.startswith('+'):
        digits = s[1:]
        return s if digits.isdigit() and 8 <= len(digits) <= 15 else None
    if not s.isdigit():
        return None
    if s.startswith('971') and _UAE_MOBILE.match(s[3:]):
        return '+' + s
    if s.startswith('0') and _UAE_MOBILE.match(s[1:]):
        return '+971' + s[1:]
    if _UAE_MOBILE.match(s):
        return '+971' + s
    return None


def _sha256(value):
    return hashlib.sha256(value.encode()).hexdigest() if value else None


def hashed_user_data(email, phone):
    return {'em': _sha256(normalize_email(email)), 'ph': _sha256(normalize_phone_ae(phone))}
