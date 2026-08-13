{
    'name': 'Techrise Website',
    'version': '18.0.2.18.0',
    'category': 'Website',
    'summary': 'Professional Website for Techrise - Your Partner in Organized Digital Transformation',
    'description': """
        Professional website module for Techrise company.
        Features:
        - Modern homepage with hero video, stats, services, industries, client showcase
        - About Us, Services, Server & Hosting, and Contact pages
        - Custom header and footer with real company info
        - SVG illustrations for service sections
        - Animated counters, card hover effects, smooth scrolling
        - Phone number and search hidden from navigation
        - Fully responsive design
        - Techrise brand colors (Blue + Gold)
    """,
    'author': 'Techrise',
    'website': 'https://techriseae.com',
    'depends': ['website', 'crm', 'website_hr_recruitment'],
    'data': [
        'views/layout.xml',
        'views/homepage.xml',
        'views/pages.xml',
        'views/industry_pages.xml',
        'views/product_pages.xml',
        'views/suite_page.xml',
        'views/jobs.xml',
        'views/seo.xml',
        'data/website_data.xml',
        'data/jobs_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'techrise_website/static/src/scss/style.scss',
            'techrise_website/static/src/js/main.js',
            'techrise_website/static/src/js/tr_hero_bg.js',
            'techrise_website/static/src/js/tr_splash_cursor.js',
            'techrise_website/static/src/js/tr_decode_text.js',
            'techrise_website/static/src/js/tr_suite.js',
            'techrise_website/static/src/js/tr_globe.js',
            'techrise_website/static/src/js/tr_fsel.js',
            'techrise_website/static/src/js/tr_clients.js',
        ],
    },
    'images': ['static/description/icon.jpg'],
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
