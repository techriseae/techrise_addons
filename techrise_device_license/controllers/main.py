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
        # Effective expiry the client should enforce (subscription wins).
        effective_expiry = ''
        if device.subscription_id:
            res['subscription'] = device.subscription_id.state
            if device.subscription_id.end_date:
                effective_expiry = fields.Date.to_string(
                    device.subscription_id.end_date)
                res['subscription_expiry'] = effective_expiry
        if not effective_expiry and device.expiry_date:
            effective_expiry = fields.Date.to_string(device.expiry_date)

        # Tamper-proof envelope: clients trust ONLY these signed fields.
        sig = request.env['techrise.license.signer'].sudo().gate_signature(
            device_uid, allowed, effective_expiry)
        if sig:
            res['sig'] = sig
        return res

    @http.route('/techrise/license/lease', type='json', auth='public',
                methods=['POST'], csrf=False)
    def license_lease(self, **kw):
        """Lease endpoint for server-side (Odoo) installations.

        An installation is modelled as a ``techrise.device`` keyed by its
        hardware ``fingerprint`` (stored in device_uid, app_id='odoo'). Unknown
        installations auto-register as ``pending`` so an admin can approve them
        from **Techrise > Licensed Devices**. The reply carries a short-lived,
        Ed25519-signed lease the client verifies and caches (see aldalil_base).
        """
        fingerprint = (kw.get('fingerprint') or '').strip()
        if not fingerprint:
            return {'allowed': False, 'reason': 'missing_fingerprint'}

        Device = request.env['techrise.device'].sudo()
        now = fields.Datetime.now()
        hostname = kw.get('hostname') or ''
        modules = kw.get('modules') or []
        note = 'Odoo install — %s\nmodules: %s\ndb_uuid: %s' % (
            hostname, ', '.join(modules) if isinstance(modules, list) else modules,
            kw.get('db_uuid') or '')

        seen_vals = {
            'last_seen': now,
            'last_ip': request.httprequest.remote_addr,
            'app_id': 'odoo',
            'device_model': hostname or 'odoo',
        }

        device = Device.search([('device_uid', '=', fingerprint)], limit=1)
        if not device:
            try:
                with request.env.cr.savepoint():
                    device = Device.create(dict(
                        seen_vals,
                        name=hostname or ('Odoo %s' % fingerprint[:8]),
                        device_uid=fingerprint,
                        state='pending',
                        first_seen=now,
                        check_count=0,
                        note=note,
                    ))
            except Exception:
                device = Device.search([('device_uid', '=', fingerprint)], limit=1)
                if not device:
                    _logger.exception('license_lease: registration failed for %s',
                                      fingerprint)
                    return {'allowed': False, 'reason': 'server_error'}

        device.write(dict(seen_vals, check_count=device.check_count + 1))
        allowed, reason = device.gate_decision()
        res = {'allowed': allowed, 'reason': reason}
        lease = request.env['techrise.license.signer'].sudo().lease_signature(
            fingerprint, allowed)
        if lease:
            res.update(lease)
        return res
