{
    'name': 'Techrise Device License',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Activation gate for Techrise mobile apps — devices must be '
               'registered and approved here before they run.',
    'description': """
Techrise Device License
=======================
Central activation registry for Techrise mobile apps (EID Reader, Healthcare).

On every launch a device calls ``POST /techrise/device/check`` with its unique
id (Android ID). The server decides whether the app is allowed to run:

* Unknown device  -> auto-registered as **Pending** (not allowed), so it shows
  up in the backend for an admin to approve.
* Pending/Blocked -> not allowed; the app refuses to open.
* Active          -> allowed (until the optional expiry date).

Approve / block devices from **Techrise > Licensed Devices**.
""",
    'author': 'Techrise',
    'website': 'https://techriseae.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/techrise_device_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
