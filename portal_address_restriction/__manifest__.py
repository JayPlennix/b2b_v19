# -*- coding: utf-8 -*-
{
    'name': 'Portal Address Restriction',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Customer account details and addresses can only be changed by Transmed staff, not by portal users.',
    'description': """
Plennix Technologies — Portal Address Restriction
=================================================

Customer names, contact details and addresses are maintained by Transmed's team.
Portal users (customers and salespersons) can see their account details and
addresses on the website but cannot change, add or remove them; they are asked to
contact support instead. Internal users keep full editing rights.

Key Features
------------
* My Account page is read-only for portal users, with a message to contact support
* No adding, editing or removing addresses on My Addresses for portal users
* No address editing from the checkout and payment pages for portal users
* Changes are also refused by the server, not only hidden on screen

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['portal', 'website_sale'],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
