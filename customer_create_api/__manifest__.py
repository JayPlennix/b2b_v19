# -*- coding: utf-8 -*-
{
    'name': 'Customer API (JDE)',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Lets JD Edwards (JDE) create and update B2B customers in Odoo automatically through an API.',
    'description': """
Plennix Technologies — Customer API (JDE)
=========================================

B2B customers are created and maintained in JD Edwards (JDE). This module lets
JDE push those customers into Odoo through a secured API: new customers are
created with their address, company, salesperson, pricelist, payment terms and
JDE classification (group, channel, area, sub-area), and later changes are
applied to the existing customer. This saves the sales team from re-keying
customers and keeps both systems consistent.

Key Features
------------
* JDE creates new B2B customers in Odoo automatically, including a delivery address when needed
* JDE updates existing customers, including archiving or re-activating them and their portal access
* Customers are matched by their JDE customer number, so duplicates are refused
* Company, payment term, pricelist, salesperson and KSA warehouse location assigned from JDE codes
* JDE classification (group, channel, area, sub-area) shown on a dedicated customer tab
* The API login returns the session id in the response so JDE can reuse it

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'crm', 'account', 'sale', 'stock'],
    'data': [
        'views/res_partner_inherit.xml',
        'views/res_company.xml',
        'views/stock_location.xml',
        'views/account_payment_term_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
