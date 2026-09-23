# -*- coding: utf-8 -*-
{
    'name': 'TM Update Products',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Updates the customer-facing product names in bulk from an Excel file, matched on the JDE item number.',
    'description': """
TM Update Products (Acespritech) — migrated to Odoo 19.0 by Plennix Technologies
================================================================================

Marketing keeps the customer-facing product names of the web shop in a
spreadsheet. This module imports that spreadsheet: for every row it finds the
product by its JD Edwards item number and updates the name customers see. It
reports how many products were updated and which item numbers were not found.

Key Features
------------
* Bulk update of the customer-facing product name from an Excel file
* Products matched on their JDE item number
* Feedback on updated products and unknown item numbers

Original module by Acespritech Solutions Pvt. Ltd.; Odoo 19.0 migration by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Acespritech Solutions Pvt. Ltd., Plennix Technologies',
    'company': 'Acespritech Solutions Pvt. Ltd.',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['product', 'stock', 'tm_website_product_name', 'product_create_api'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_update_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
