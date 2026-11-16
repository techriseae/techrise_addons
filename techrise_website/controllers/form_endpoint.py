import logging

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm

_logger = logging.getLogger(__name__)

# Odoo's /website/form/<model> route has csrf=False and no spam guard. The site
# collects leads only through /contact/submit (honeypot + signed timestamp), so
# the native endpoint stays open only for models a page really uses (job
# applications on /jobs use hr.applicant).
BLOCKED_FORM_MODELS = {'crm.lead', 'mail.mail', 'project.task'}


class TechriseWebsiteForm(WebsiteForm):

    @http.route()
    def website_form(self, model_name, **kwargs):
        if model_name in BLOCKED_FORM_MODELS:
            _logger.info("native website form blocked: %s from %s",
                         model_name, request.httprequest.remote_addr)
            return request.make_json_response({'error': 'This form is not available.'}, status=403)
        return super().website_form(model_name, **kwargs)
