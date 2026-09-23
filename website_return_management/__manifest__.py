# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#    Odoo 19.0 migration: Plennix Technologies (https://www.plennix.com)
#
#    This program is free software: you can modify it under the terms of the GNU
#    AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
################################################################################
{
    'name': 'Website Return Order Management',
    'version': '19.0.1.0.1',
    'category': 'Website',
    'summary': 'Lets web shop customers request returns of delivered products, and staff process them as return transfers.',
    'description': """
Website Return Order Management (Cybrosys) — migrated to Odoo 19.0 by Plennix Technologies
==========================================================================================

Customers request the return of products they have received from their order in
the portal. Each request becomes a return order that staff confirm, which creates
the return transfer and notifies the salesperson. Customers follow their return
requests in the portal.

Key Features
------------
* Return request from the customer portal, limited to the quantity actually delivered
* Return reasons configurable in Sales
* Return orders with the return and delivery transfers, quantities and amounts
* Return order confirmation email to the salesperson, and a printable return order
* Return counts on the customer and the sales order

Original module by Cybrosys Techno Solutions; Odoo 19.0 migration by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Cybrosys Techno Solutions, Plennix Technologies',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': ['website_sale', 'stock', 'sale_management', 'custom_saleorder_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence.xml',
        'data/mail_template_data.xml',
        'views/website_thankyou_templates.xml',
        'views/sale_return_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/return_reason.xml',
        'views/stock_picking_views.xml',
        'report/sale_return_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_return_management/static/src/js/sale_return.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
