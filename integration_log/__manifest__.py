# -*- coding: utf-8 -*-
{
    'name': 'Integration Log',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Central record of every request exchanged with JD Edwards (JDE) and the HyperPay / Apple Pay payment gateways.',
    'description': """
Plennix Technologies — Integration Log
======================================

Gives administrators one place to see every message Odoo exchanges with external
systems: the JD Edwards (JDE) ERP (orders, stock availability, deliveries, order
tracking, delivery schedules) and the HyperPay / Apple Pay payment gateways. Each
entry keeps the address called, the data sent and the reply received, so failed
orders, payments or synchronisations can be investigated without server access.

Key Features
------------
* One searchable list of all calls to JDE and the payment gateways
* Address, headers, data sent and reply received kept for each call
* Entries are read-only on screen, so the history cannot be altered by mistake
* Newest entries shown first
* Visible to administrators only, since entries can contain access tokens and payment data

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/integration_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
