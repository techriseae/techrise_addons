from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


SERVICE_LABELS = {
    'erp': 'ERP System Design (Odoo)',
    'website': 'Website Design & Development',
    'mobile': 'Mobile App Development',
    'integration': 'System Integration',
    'accounting': 'Accounting & Tax Services',
    'branding': 'Branding & Marketing',
    'hosting': 'Server & Hosting',
    'support': 'Technical Support',
    'other': 'Other',
    # Product landing pages — keep distinct from the generic 'accounting'
    # service so we can attribute leads to the dedicated landing page.
    'accounting_software': 'Accounting Software (Landing Page)',
    'hr_software': 'HR & Payroll Software (Landing Page)',
    'call_center_software': 'Call Center Software (Landing Page)',
    'inventory_procurement': 'Inventory & Procurement (Landing Page)',
    'full_erp_suite': 'Full ERP Suite (Landing Page)',
    'custom_software': 'Custom Software Development (Landing Page)',
}


class TechriseWebsite(http.Controller):

    @http.route('/about', type='http', auth='public', website=True, sitemap=True)
    def about_page(self, **kwargs):
        return request.render('techrise_website.about_page')

    @http.route('/services', type='http', auth='public', website=True, sitemap=True)
    def services_page(self, **kwargs):
        return request.render('techrise_website.services_page')

    @http.route('/server', type='http', auth='public', website=True, sitemap=True)
    def server_page(self, **kwargs):
        return request.render('techrise_website.server_page')

    @http.route('/contactus', type='http', auth='public', website=True, sitemap=True)
    def contact_page(self, **kwargs):
        return request.render('techrise_website.contact_page')

    @http.route('/contact', type='http', auth='public', website=True, sitemap=False)
    def contact_alias(self, **kwargs):
        # Canonical URL is /contactus; 301 kills the duplicate-content signal in GSC.
        return redirect('/contactus', code=301)

    @http.route('/ar/contact', type='http', auth='public', website=True, sitemap=False)
    def contact_alias_ar(self, **kwargs):
        # Preserve language: /ar/contact → /ar/contactus (not /contactus which drops to English).
        return redirect('/ar/contactus', code=301)

    # ================================================================
    # Legacy /ar_001 → /ar single-hop redirects.
    # Odoo's native middleware 301s /ar_001/* to /ar/*, but for the
    # bare root it produces /ar/ which then 301s to /ar — a 2-hop
    # chain that GSC flags as "Page with redirect". These routes
    # collapse the chain to one hop so legacy URLs in Google's index
    # resolve in a single redirect.
    # ================================================================
    @http.route(['/ar_001', '/ar_001/'], type='http', auth='public', website=False, sitemap=False)
    def ar_001_root_redirect(self, **kwargs):
        return redirect('/ar', code=301)

    @http.route('/ar_001/<path:subpath>', type='http', auth='public', website=False, sitemap=False)
    def ar_001_subpath_redirect(self, subpath, **kwargs):
        # Map legacy /ar_001/contact directly to /ar/contactus (single hop instead of three).
        if subpath.rstrip('/') == 'contact':
            return redirect('/ar/contactus', code=301)
        return redirect('/ar/' + subpath.lstrip('/'), code=301)

    @http.route('/contact/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_submit(self, **kwargs):
        name = kwargs.get('name', '').strip()
        email = kwargs.get('email_from', '').strip()
        phone = kwargs.get('phone', '').strip()
        company = kwargs.get('company', '').strip()
        service_key = kwargs.get('service', '').strip()
        message = kwargs.get('body', '').strip()

        service_label = SERVICE_LABELS.get(service_key, service_key)

        lead_name = f"Website Contact: {name}"
        if service_label:
            lead_name = f"{service_label} - {name}"

        description = message
        if service_label:
            description = f"Service Interested In: {service_label}\n\n{message}"

        vals = {
            'name': lead_name,
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'partner_name': company or False,
            'description': description,
            'type': 'lead',
        }

        request.env['crm.lead'].sudo().create(vals)

        return request.render('techrise_website.contact_thankyou')

    @http.route('/privacy-policy', type='http', auth='public', website=True, sitemap=True)
    def privacy_policy_page(self, **kwargs):
        return request.render('techrise_website.privacy_policy_page')

    @http.route('/terms-and-conditions', type='http', auth='public', website=True, sitemap=True)
    def terms_and_conditions_page(self, **kwargs):
        return request.render('techrise_website.terms_and_conditions_page')

    # ================================================================
    # Industry landing pages (Google Ads + SEO targeted)
    # ================================================================
    @http.route('/erp-for-construction-uae', type='http', auth='public', website=True, sitemap=True)
    def erp_construction_page(self, **kwargs):
        return request.render('techrise_website.erp_construction_page')

    @http.route('/erp-for-healthcare-uae', type='http', auth='public', website=True, sitemap=True)
    def erp_healthcare_page(self, **kwargs):
        return request.render('techrise_website.erp_healthcare_page')

    @http.route('/erp-for-retail-uae', type='http', auth='public', website=True, sitemap=True)
    def erp_retail_page(self, **kwargs):
        return request.render('techrise_website.erp_retail_page')

    # ================================================================
    # Product landing pages (Google Ads + Meta + SEO targeted)
    # One page per software product — distinct intent from the
    # industry pages above (which target sector keywords).
    # ================================================================
    @http.route('/erp-suite', type='http', auth='public', website=True, sitemap=True)
    def techrise_suite_page(self, **kwargs):
        return request.render('techrise_website.techrise_suite_page')

    @http.route('/accounting-software-uae', type='http', auth='public', website=True, sitemap=True)
    def accounting_software_page(self, **kwargs):
        return request.render('techrise_website.accounting_software_page')

    @http.route('/hr-payroll-software-uae', type='http', auth='public', website=True, sitemap=True)
    def hr_payroll_software_page(self, **kwargs):
        return request.render('techrise_website.hr_payroll_software_page')

    @http.route('/call-center-software-uae', type='http', auth='public', website=True, sitemap=True)
    def call_center_software_page(self, **kwargs):
        return request.render('techrise_website.call_center_software_page')

    @http.route('/inventory-procurement-uae', type='http', auth='public', website=True, sitemap=True)
    def inventory_procurement_page(self, **kwargs):
        return request.render('techrise_website.inventory_procurement_page')

    @http.route('/erp-software-uae', type='http', auth='public', website=True, sitemap=True)
    def full_erp_suite_page(self, **kwargs):
        return request.render('techrise_website.full_erp_suite_page')

    @http.route('/custom-software-uae', type='http', auth='public', website=True, sitemap=True)
    def custom_software_page(self, **kwargs):
        return request.render('techrise_website.custom_software_page')
