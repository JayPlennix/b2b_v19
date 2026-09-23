# -*- coding: utf-8 -*-
{
    'name': 'Website Hide Prices',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Hides prices and ordering on the web shop from visitors who are not logged in.',
    'description': """
Plennix Technologies — Website Hide Prices
==========================================

Transmed sells to businesses at customer-specific prices, which should not be
visible to the public. This module hides every price on the web shop from
visitors who are not logged in, and invites them to log in. Products stay
browsable, but only customers see prices and can order.

Key Features
------------
* Prices hidden on the shop, the product page and the product snippets for visitors
* "Log in to see prices" invitation instead of the price and the add-to-cart button
* Adding to the cart refused for visitors, also when called directly

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'custom_website'],
    'data': ['views/website_templates.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
