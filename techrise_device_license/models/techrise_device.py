from odoo import fields, models


class TechriseDevice(models.Model):
    _name = 'techrise.device'
    _description = 'Techrise Licensed Device'
    _inherit = ['mail.thread']
    _order = 'last_seen desc, id desc'

    name = fields.Char(
        string='Label', required=True, tracking=True,
        help='Friendly name for this device, e.g. "Al Dalil — Reception 1".')
    device_uid = fields.Char(
        string='Device UID', required=True, copy=False, index=True,
        help='Stable per-device identifier reported by the app (Android ID).')
    state = fields.Selection(
        [('pending', 'Pending'), ('active', 'Active'), ('blocked', 'Blocked')],
        string='Status', default='pending', required=True, tracking=True,
        help='Pending: seen but not yet approved (app blocked).\n'
             'Active: approved, app allowed to run.\n'
             'Blocked: explicitly denied.')
    app_id = fields.Char(
        string='App', help='Reporting application id, e.g. com.techrise.eidreader.')
    app_version = fields.Char(string='App Version')
    device_model = fields.Char(string='Device Model')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    expiry_date = fields.Date(
        string='Expiry Date',
        help='Optional. When set, the device stops being allowed after this date.')
    first_seen = fields.Datetime(string='First Seen', readonly=True)
    last_seen = fields.Datetime(string='Last Seen', readonly=True)
    last_ip = fields.Char(string='Last IP', readonly=True)
    check_count = fields.Integer(string='Check Count', readonly=True, default=0)
    note = fields.Text(string='Notes')

    _sql_constraints = [
        ('device_uid_uniq', 'unique(device_uid)',
         'A device with this UID is already registered.'),
    ]

    def _is_expired(self):
        self.ensure_one()
        return bool(self.expiry_date
                    and self.expiry_date < fields.Date.context_today(self))

    def gate_decision(self):
        """Return ``(allowed: bool, reason: str)`` for the activation gate."""
        self.ensure_one()
        if self.state == 'blocked':
            return False, 'blocked'
        if self.state == 'pending':
            return False, 'pending_registration'
        if self._is_expired():
            return False, 'expired'
        return True, 'active'

    def action_approve(self):
        self.write({'state': 'active'})

    def action_block(self):
        self.write({'state': 'blocked'})

    def action_set_pending(self):
        self.write({'state': 'pending'})
