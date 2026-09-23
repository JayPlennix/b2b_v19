# -*- coding: utf-8 -*-
{
    'name': 'JDE Connection & Stock Availability',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Connects Odoo to JD Edwards (JDE) and keeps web shop stock in line with JDE availability.',
    'description': """
Plennix Technologies — JDE Connection & Stock Availability
==========================================================

Holds each company's JD Edwards (JDE) login, which every Transmed JDE
integration uses, and keeps the stock shown on the B2B web shop in line with
JDE. Every 20 minutes Odoo fetches the stock that changed in JDE, and whenever a
customer opens a product page, the cart or the checkout, the stock of those
products is refreshed live from JDE, so customers only order what is really
available. In KSA, stock is recorded per lot with its expiry date.

Key Features
------------
* One place to configure the JDE login for each company, with a connection test
* Stock that changed in JDE is updated in Odoo every 20 minutes
* Live stock refresh from JDE on product page, cart and checkout
* KSA stock per warehouse and lot, with expiry date
* Every JDE call recorded in the integration log

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'crm',
        'sale',
        'stock',
        'product_expiry',
        'website',
        'website_sale',
        'integration_log',
        'customer_create_api',
    ],
    'data': [
        'data/scheduled_action.xml',
        'views/res_config_setting_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
