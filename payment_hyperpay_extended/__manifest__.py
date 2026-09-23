# -*- coding: utf-8 -*-
{
    'name': 'Hyperpay Payment Acquirer Extended',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Captures the pre-authorized HyperPay / Apple Pay payment of a web order once JD Edwards has invoiced it.',
    'description': """
Plennix Technologies — Hyperpay Payment Acquirer Extended
=========================================================

Web shop orders paid with HyperPay or Apple Pay are only pre-authorized at
checkout, because the final amount is known once JD Edwards (JDE) has delivered
and invoiced the order. This module captures the amount invoiced by JDE on the
customer's pre-authorization at that moment, using Odoo's standard capture, so
the payment is posted automatically. Orders pre-authorized before the upgrade to
Odoo 19 are captured as well.

Key Features
------------
* Automatic capture of the JDE invoiced amount on the customer's pre-authorization
* Payment posted by Odoo and linked to the sales order
* "Payment Done" indicator on the sales order
* Orders pre-authorized in Odoo 17 still captured after the upgrade
* Single-use payment references are never offered as saved cards

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['sale', 'payment_hyperpay', 'integration_log'],
    'data': [
        'views/sale_order.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
