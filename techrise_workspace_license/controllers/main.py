# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class TechriseWorkspaceController(http.Controller):

    @http.route('/techrise/workspace/check', type='json', auth='public',
                methods=['POST'], csrf=False)
    def workspace_check(self, **kw):
        """Licence status for a client workspace (TechRise HR mobile app).

        params: db_uuid (required), server_url, db_name, company_name,
                app_id, app_version, api_version.
        Unknown db_uuid → registered as a 30-day trial.
        """
        return request.env['techrise.workspace'].sudo()._check(
            kw, request.httprequest.remote_addr)
