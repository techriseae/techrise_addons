from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TechriseSubscription(models.Model):
    _name = 'techrise.subscription'
    _description = 'Techrise License Subscription'
    _inherit = ['mail.thread']
    _order = 'end_date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False, index=True,
        default=lambda self: _('New'), tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True,
        help='The clinic / customer this subscription belongs to.')
    plan = fields.Selection(
        [('trial', 'Trial'), ('standard', 'Standard'), ('premium', 'Premium')],
        string='Plan', default='standard', required=True, tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active'),
         ('suspended', 'Suspended'), ('expired', 'Expired')],
        string='Status', default='draft', required=True, tracking=True,
        help='Draft: not yet activated (devices blocked).\n'
             'Active: devices allowed until the expiry date.\n'
             'Suspended: temporarily disabled.\n'
             'Expired: past the expiry date.')
    start_date = fields.Date(
        string='Start Date', default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(
        string='Expiry Date', tracking=True,
        help='After this date the subscription (and all its devices) stop '
             'being allowed. Leave empty for no expiry.')
    seat_count = fields.Integer(
        string='Device Seats', default=1, required=True, tracking=True,
        help='Maximum number of *active* devices allowed under this subscription.')

    device_ids = fields.One2many(
        'techrise.device', 'subscription_id', string='Devices')
    device_count = fields.Integer(
        string='Devices', compute='_compute_seat_usage')
    seats_used = fields.Integer(
        string='Seats Used', compute='_compute_seat_usage')
    seats_available = fields.Integer(
        string='Seats Available', compute='_compute_seat_usage')
    note = fields.Text(string='Notes')

    @api.depends('device_ids.state', 'seat_count')
    def _compute_seat_usage(self):
        for sub in self:
            active = sub.device_ids.filtered(lambda d: d.state == 'active')
            sub.device_count = len(sub.device_ids)
            sub.seats_used = len(active)
            sub.seats_available = sub.seat_count - len(active)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'techrise.subscription') or _('New')
        return super().create(vals_list)

    @api.constrains('seat_count')
    def _check_seat_count(self):
        for sub in self:
            if sub.seat_count < 0:
                raise ValidationError(_('Device seats cannot be negative.'))

    def _is_expired(self):
        self.ensure_one()
        return bool(self.end_date
                    and self.end_date < fields.Date.context_today(self))

    def is_valid(self):
        """True when the subscription currently authorises its devices."""
        self.ensure_one()
        return self.state == 'active' and not self._is_expired()

    def subscription_reason(self):
        """Gate reason code; ``'active'`` when valid."""
        self.ensure_one()
        if self.state == 'suspended':
            return 'subscription_suspended'
        if self.state == 'expired' or self._is_expired():
            return 'subscription_expired'
        if self.state == 'draft':
            return 'subscription_inactive'
        return 'active'

    def action_activate(self):
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_renew(self):
        """Re-activate; the admin adjusts the new expiry date manually."""
        self.write({'state': 'active'})

    @api.model
    def _cron_expire_subscriptions(self):
        today = fields.Date.context_today(self)
        self.search([('state', '=', 'active'),
                     ('end_date', '!=', False),
                     ('end_date', '<', today)]).write({'state': 'expired'})
