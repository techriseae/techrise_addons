{
    'name': 'Techrise Workspace License',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Per-workspace licensing for the TechRise HR mobile app — '
               '30-day trial from first use, then activation.',
    'author': 'Techrise',
    'website': 'https://techriseae.com',
    'depends': ['techrise_device_license', 'mail'],
    'external_dependencies': {'python': ['cryptography']},
    'data': [
        'security/ir.model.access.csv',
        'data/techrise_workspace_data.xml',
        'views/techrise_workspace_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
