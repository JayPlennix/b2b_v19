# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# Migrated to Odoo 19.0 by Plennix Technologies for its licensee (Transmed),
# under the licensee's Webkul license. Not for redistribution.
#################################################################################
{
    'name': 'Hyperpay Payment Acquirer',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Lets web shop customers pay by card or mada through HyperPay, pre-authorized at checkout and captured later.',
    'description': """
Hyperpay Payment Acquirer (Webkul) — migrated to Odoo 19.0 by Plennix Technologies
==================================================================================

Adds HyperPay as an online payment provider. Customers pay by card (Visa,
Mastercard) or mada on a secure HyperPay payment page. With "Capture Amount
Manually" the amount is only pre-authorized at checkout and captured later, for
the final invoiced amount, using Odoo's standard capture, void and refund
actions.

Key Features
------------
* Card and mada payments through the HyperPay COPYandPAY payment page
* Pre-authorization at checkout, capture of the final amount later (full or partial)
* Standard Odoo Capture, Void and Refund actions sent to HyperPay
* Every HyperPay call recorded in the integration log

Original module by Webkul Software Pvt. Ltd.; Odoo 19.0 migration by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Webkul Software Pvt. Ltd., Plennix Technologies',
    'company': 'Webkul Software Pvt. Ltd.',
    'maintainer': 'Plennix Technologies',
    'website': 'https://store.webkul.com/odoo-hyperpay-payment-acquirer.html',
    'license': 'Other proprietary',
    'depends': ['payment', 'account_payment', 'website_sale', 'integration_log'],
    'data': [
        'views/payment_hyperpay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
