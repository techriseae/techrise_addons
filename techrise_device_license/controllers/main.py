import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TechriseDeviceController(http.Controller):

    @http.route('/techrise/device/check', type='json', auth='public',
                methods=['POST'], csrf=False)
    def device_check(self, **kw):
        """Activation gate — called by Techrise apps on every launch.

        params: device_uid (required), app_id, app_version, device_model.
        returns: {allowed, reason, device_uid, name, [expiry]}.

        An unknown device is auto-registered as ``pending`` (not allowed) so an
        admin can approve it from the backend. The decision itself lives in
        ``techrise.device.gate_decision()``.
        """
        device_uid = (kw.get('device_uid') or '').strip()
        if not device_uid:
            return {'allowed': False, 'reason': 'missing_device_uid'}

        Device = request.env['techrise.device'].sudo()
        now = fields.Datetime.now()

        seen_vals = {'last_seen': now, 'last_ip': request.httprequest.remote_addr}
        for key in ('app_id', 'app_version', 'device_model'):
            if kw.get(key):
                seen_vals[key] = kw[key]

        device = Device.search([('device_uid', '=', device_uid)], limit=1)
        if not device:
            create_vals = dict(
                seen_vals,
                name=kw.get('device_model') or device_uid,
                device_uid=device_uid,
                state='pending',
                first_seen=now,
                check_count=0,
            )
            try:
                # savepoint so a concurrent first-contact from the same device
                # (unique constraint hit) doesn't poison the whole request.
                with request.env.cr.savepoint():
                    device = Device.create(create_vals)
            except Exception:
                device = Device.search([('device_uid', '=', device_uid)], limit=1)
                if not device:
                    _logger.exception(
                        "device_check: registration failed for %s", device_uid)
                    return {'allowed': False, 'reason': 'server_error'}

        device.write(dict(seen_vals, check_count=device.check_count + 1))
        allowed, reason = device.gate_decision()
        res = {
            'allowed': allowed,
            'reason': reason,
            'device_uid': device_uid,
            'name': device.name,
        }
        if device.expiry_date:
            res['expiry'] = fields.Date.to_string(device.expiry_date)
        return res
