# -*- coding: utf-8 -*-
{
    'name': 'Website Product Name Edit',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Shows a customer-facing product name on the web shop, and what is already in the cart per unit.',
    'description': """
Plennix Technologies — Website Product Name Edit
================================================

Products are named for internal use, which is not always what customers should
read on the web shop. This module adds a customer-facing name, shown on the
product page and in the shop when it is filled in. On the product page it also
tells customers what they already have in their cart, per unit of measure, so
they can see they already ordered, for example, 2 boxes and 5 units.

Key Features
------------
* Customer-facing product name used on the product page and shop
* "Already in your cart" message split per unit of measure

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['product', 'website_sale', 'website_sale_stock'],
    'data': [
        'views/product_view.xml',
        'views/template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tm_website_product_name/static/src/xml/product_availability.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
