# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2023. All rights reserved.
# Migrated to Odoo 19.0 by Plennix Technologies for its licensee (Transmed),
# under the licensee's purchased license. Not for redistribution.
{
    'name': 'Hyperpay Payment Acquirer - Applepay',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Lets web shop customers pay with Apple Pay through HyperPay, pre-authorized at checkout and captured later.',
    'description': """
Hyperpay Payment Acquirer - Applepay (Technaureus) — migrated to Odoo 19.0 by Plennix Technologies
==================================================================================================

Adds Apple Pay, processed by HyperPay, as an online payment provider. Customers
pay with Apple Pay on the HyperPay payment page. With "Capture Amount Manually"
the amount is only pre-authorized at checkout and captured later, for the final
invoiced amount, with Odoo's standard capture, void and refund actions.

Key Features
------------
* Apple Pay payments through HyperPay with its own HyperPay entity
* Pre-authorization at checkout, capture of the final amount later (full or partial)
* Apple Pay sheet settings (display name, merchant identifier, networks, countries) in the provider
* Every HyperPay call recorded in the integration log

Original module by Technaureus Info Solutions Pvt. Ltd.; Odoo 19.0 migration by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd., Plennix Technologies',
    'company': 'Technaureus Info Solutions Pvt. Ltd.',
    'maintainer': 'Plennix Technologies',
    'website': 'http://www.technaureus.com/',
    'license': 'OPL-1',
    'depends': ['payment_hyperpay', 'payment_hyperpay_extended', 'integration_log'],
    'data': [
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
