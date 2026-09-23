# -*- coding: utf-8 -*-
{
    'name': 'Delivery Scheduler',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Keeps each B2B customer\'s delivery days and validity dates in sync with JD Edwards (JDE).',
    'description': """
Plennix Technologies — Delivery Scheduler
=========================================

Brings the customer delivery schedules maintained in JD Edwards (JDE) into Odoo.
Every two hours Odoo asks JDE, for each company that has the integration set up,
which weekdays each B2B customer can receive deliveries and between which dates
that schedule applies, and stores the result against the customer. The eCommerce
team can review these schedules in Odoo without logging into JDE.

Key Features
------------
* Automatic synchronisation of customer delivery schedules from JDE every two hours
* Delivery weekdays, delivery code, effective date and expiry date stored per customer
* Schedules listed under the eCommerce configuration menu for review and correction
* Every JDE call recorded in the integration log for troubleshooting

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'website',
        'website_sale',
        'integration_log',
        'customer_create_api',
        'checkavailability_integration_jde',
        'custom_saleorder_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/delivery_scheduler_view.xml',
        'data/data.xml',
        'data/scheduled_action.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
