# -*- coding: utf-8 -*-
"""Workspace status envelopes signed with the central Ed25519 key.

Reuses ``techrise.license.signer`` from techrise_device_license (private key
path from ``techrise_license.signing_key_path``). Clients — the TechRise HR
app and techrise_mobile_api on client instances — embed the public key and
verify this exact message layout.
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

WORKSPACE_PREFIX = 'techrise-workspace:v1'


def _workspace_message(db_uuid, status, ends, iat):
    return '\n'.join([
        WORKSPACE_PREFIX,
        db_uuid or '',
        status or '',
        ends or '',
        str(iat),
    ]).encode('utf-8')


class TechriseLicenseSigner(models.AbstractModel):
    _inherit = 'techrise.license.signer'

    @api.model
    def workspace_signature(self, db_uuid, status, ends):
        """Return ``{'iat', 'sig'}`` or None when the key is unavailable."""
        iat = int(fields.Datetime.now().timestamp())
        try:
            sig = self._sign(_workspace_message(db_uuid, status, ends, iat))
        except Exception as exc:  # key missing/unreadable: answer unsigned, log loudly
            _logger.error('Workspace licence signing unavailable: %s', exc)
            return None
        return {'iat': iat, 'sig': sig}
