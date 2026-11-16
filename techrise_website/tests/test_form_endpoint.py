from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestNativeFormEndpoint(HttpCase):
    """Odoo's /website/form/<model> has csrf=False: bots can create leads/emails
    without ever loading our guarded contact form. The site doesn't use it for
    crm.lead / mail.mail / project.task, so those are closed."""

    def _post(self, model):
        return self.url_open(f'/website/form/{model}', data={
            'contact_name': 'Bot', 'email_from': 'bot@example.com',
            'name': 'spam', 'description': 'buy now', 'email_to': 'x@example.com',
            'subject': 'spam', 'body_html': 'spam',
        })

    def test_lead_cannot_be_created_through_native_form(self):
        before = self.env['crm.lead'].sudo().search_count([])
        res = self._post('crm.lead')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.env['crm.lead'].sudo().search_count([]), before)

    def test_mail_cannot_be_sent_through_native_form(self):
        before = self.env['mail.mail'].sudo().search_count([])
        res = self._post('mail.mail')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.env['mail.mail'].sudo().search_count([]), before)

    def test_job_applications_still_reach_the_native_form(self):
        res = self._post('hr.applicant')
        self.assertNotEqual(res.status_code, 403)
