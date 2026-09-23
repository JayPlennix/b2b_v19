# -*- coding: utf-8 -*-
{
    'name': 'Product API (JDE)',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Lets JD Edwards (JDE) create and update products, stock, lots, packagings and customer pricelists in Odoo.',
    'description': """
Plennix Technologies — Product API (JDE)
========================================

Products, stock levels and customer prices are maintained in JD Edwards (JDE).
This module lets JDE push them into Odoo through a secured API: new items are
created with their category, website category, brand, unit, packagings, taxes
and stock, later changes update the existing product, KSA stock is recorded per
lot with its expiry date, and customer-specific price lists are created and
assigned to the customer. The B2B shop always shows JDE's current catalogue,
stock and prices without manual data entry.

Key Features
------------
* JDE creates and updates products, including categories, brand, unit and taxes
* Stock quantities from JDE are recorded in the matching Odoo location
* KSA stock tracked by lot with expiry date
* JDE packages (box, carton, ...) become product packagings usable in sales
* Customer-specific price lists with dated fixed prices, assigned to the customer and their contacts
* JDE product details (family, item type, brand, supplier, storage) on a dedicated product tab

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
        'account',
        'stock',
        'stock_delivery',
        'product_expiry',
        'website',
        'website_sale',
        'website_sale_stock',
        'customer_create_api',
        'custom_saleorder_management',
    ],
    'data': [
        'views/product_template_inherit.xml',
        'views/product_pricelist_inherit.xml',
        'views/product_category.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
