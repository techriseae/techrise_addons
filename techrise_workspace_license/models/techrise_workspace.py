# -*- coding: utf-8 -*-
import logging
import unicodedata
from datetime import timedelta

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

STATES = [
    ('trial', 'Trial'),
    ('active', 'Active'),
    ('expired', 'Expired'),
    ('blocked', 'Blocked'),
]


MAX_APP_VERSIONS = 20          # distinct app versions remembered per workspace
MAX_TEXT = 255                 # name / db_name / app_version / db_uuid
MAX_URL = 1024                 # server_url


def _clean(value, maxlen=MAX_TEXT):
    """Coerce any JSON value to a stripped, length-capped string."""
    return str(value or '').strip()[:maxlen]


class TechriseWorkspace(models.Model):
    """One client Odoo database licensed for the TechRise HR mobile app.

    Identity is the client's ``database.uuid`` — a URL change does not
    reset the trial. ``state`` is what an admin sees and sets; the truth
    handed to clients is ``_effective_status()`` which also accounts for
    dates having passed since the last cron run.
    """
    _name = 'techrise.workspace'
    _description = 'Techrise Licensed Workspace'
    _inherit = ['mail.thread']
    _order = 'last_seen desc nulls last, id desc'

    name = fields.Char(string='Company', required=True, tracking=True)
    db_uuid = fields.Char(string='Database UUID', required=True, index=True, copy=False)
    server_url = fields.Char(string='Server URL')
    db_name = fields.Char(string='Database')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    subscription_id = fields.Many2one('techrise.subscription', string='Subscription')
    state = fields.Selection(STATES, default='trial', required=True, tracking=True)
    trial_start = fields.Date(default=fields.Date.context_today)
    trial_end = fields.Date(
        compute='_compute_trial_end', store=True, readonly=False,
        help='Computed once from Trial Start; edit directly to extend or shorten.')
    licence_end = fields.Date(string='Licence End', tracking=True,
                              help='Blank = perpetual once active.')
    first_seen = fields.Datetime(readonly=True)
    last_seen = fields.Datetime(readonly=True)
    last_ip = fields.Char(readonly=True)
    check_count = fields.Integer(readonly=True, default=0)
    app_versions = fields.Char(string='App Versions Seen', readonly=True)
    note = fields.Text()

    _sql_constraints = [
        ('db_uuid_unique', 'unique(db_uuid)', 'This database is already registered.'),
    ]

    @api.model
    def _trial_days(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'techrise_workspace.trial_days', '30')
        try:
            return max(int(raw), 0)
        except (TypeError, ValueError):
            return 30

    @api.depends('trial_start')
    def _compute_trial_end(self):
        days = self._trial_days()
        for ws in self:
            if ws.trial_start and not ws.trial_end:
                ws.trial_end = ws.trial_start + timedelta(days=days)

    # -- status -----------------------------------------------------------
    def _effective_status(self, today=None):
        self.ensure_one()
        today = today or fields.Date.context_today(self)
        if self.state == 'blocked':
            return 'blocked'
        if self.state == 'expired':
            return 'expired'
        if self.state == 'active':
            if self.licence_end and self.licence_end < today:
                return 'expired'
            return 'active'
        # trial
        if self.trial_end and self.trial_end < today:
            return 'expired'
        return 'trial'

    def _ends_date(self, today=None):
        """Date the current status ends, or False (perpetual / blocked)."""
        self.ensure_one()
        status = self._effective_status(today)
        if status == 'trial':
            return self.trial_end
        if status == 'active':
            return self.licence_end or False
        if status == 'expired':
            return self.licence_end or self.trial_end
        return False

    def _days_left(self, today):
        """Days until ``_ends_date()``: 0 when over, -1 when perpetual."""
        self.ensure_one()
        ends = self._ends_date(today)
        if not ends:
            return -1 if self._effective_status(today) == 'active' else 0
        return max((ends - today).days, 0)

    # -- admin actions ----------------------------------------------------
    def action_activate(self):
        today = fields.Date.context_today(self)
        if any(ws.licence_end and ws.licence_end < today for ws in self):
            raise UserError('Set a future licence end date or clear it before activating.')
        self.write({'state': 'active'})

    def action_block(self):
        self.write({'state': 'blocked'})

    def action_reset_to_trial(self):
        # trial_end is set explicitly: fields present in ``vals`` are not
        # recomputed during write, so relying on _compute_trial_end here
        # would leave a perpetual trial (trial_end = False).
        # licence_end is cleared too: a stale value from a previous active
        # period would otherwise leak into _ends_date() once the new trial
        # expires (expired prefers licence_end over trial_end).
        today = fields.Date.context_today(self)
        self.write({'state': 'trial', 'trial_start': today,
                    'trial_end': today + timedelta(days=self._trial_days()),
                    'licence_end': False})

    @api.model
    def _cron_expire(self):
        today = fields.Date.context_today(self)
        for ws in self.search([('state', 'in', ('trial', 'active'))]):
            if ws._effective_status(today) == 'expired':
                ws.state = 'expired'

    # -- client check -----------------------------------------------------
    @api.model
    def _check(self, payload, ip):
        """Register-or-touch the workspace and build the status response.

        Called by the public controller. Never raises for bad input — the
        app shows whatever comes back. Every payload value is coerced to a
        capped string; writes run without chatter/tracking so anonymous
        checks leave no mail rows behind.
        """
        raw_uuid = str(payload.get('db_uuid') or '')
        db_uuid = _clean(raw_uuid)
        if not db_uuid or any(
                char.isspace() or unicodedata.category(char) in ('Cc', 'Cf')
                for char in raw_uuid):
            return {'verified': False, 'status': 'unknown', 'reason': 'missing_db_uuid'}
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)
        Workspace = self.sudo().with_context(
            mail_create_nolog=True, mail_create_nosubscribe=True, tracking_disable=True)
        ws = Workspace.search([('db_uuid', '=', db_uuid)], limit=1)
        company = _clean(payload.get('company_name'))
        server_url = _clean(payload.get('server_url'), MAX_URL)
        db_name = _clean(payload.get('db_name'))
        app_version = _clean(payload.get('app_version')).replace(',', '')
        touch = {'last_seen': now, 'last_ip': _clean(ip)}
        if server_url:
            touch['server_url'] = server_url
        if db_name:
            touch['db_name'] = db_name
        if company:
            touch['name'] = company
        if not ws:
            try:
                with self.env.cr.savepoint():
                    ws = Workspace.create(dict(
                        touch, db_uuid=db_uuid, name=company or db_uuid[:8],
                        first_seen=now, trial_start=today, check_count=0))
            except psycopg2.IntegrityError:  # lost a race with a parallel first check
                # REPEATABLE READ cannot see the winning transaction in this
                # snapshot. Let the next request touch its persisted workspace.
                trial_days = self._trial_days()
                ends = (today + timedelta(days=trial_days)).isoformat()
                res = {
                    'verified': True, 'status': 'trial',
                    'company': company or db_uuid[:8], 'ends': ends,
                    'days_left': trial_days, 'read_only': False, 'db_uuid': db_uuid,
                }
                sig = self.env['techrise.license.signer'].sudo().workspace_signature(
                    db_uuid, 'trial', ends)
                if sig:
                    res.update(sig)
                _logger.info('Concurrent workspace registration for db_uuid %s; '
                             'returning virtual trial', db_uuid)
                return res
        versions = [v for v in (ws.app_versions or '').split(',') if v]
        if app_version:
            # most-recently-seen last; bounded so a chatty client cannot grow the field
            versions = [v for v in versions if v != app_version] + [app_version]
            versions = versions[-MAX_APP_VERSIONS:]
        # drop the oldest entries (never cut a token) until the joined list fits
        while len(versions) > 1 and len(','.join(versions)) > MAX_TEXT:
            versions.pop(0)
        ws.write(dict(touch, check_count=ws.check_count + 1,
                      app_versions=','.join(versions)))
        status = ws._effective_status(today)
        ends = ws._ends_date(today)
        ends_str = ends.isoformat() if ends else ''
        res = {
            'verified': status != 'blocked',
            'status': status,
            'company': ws.name,
            'ends': ends_str,
            'days_left': ws._days_left(today),
            'read_only': status == 'expired',
            'db_uuid': db_uuid,
        }
        sig = self.env['techrise.license.signer'].sudo().workspace_signature(
            db_uuid, status, ends_str)
        if sig:
            res.update(sig)
        return res
