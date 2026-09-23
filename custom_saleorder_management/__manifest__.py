{
    'name': 'Custom Sale Order Management (JDE)',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Sends B2B shop orders to JD Edwards (JDE) and keeps deliveries, prices, invoices, returns and tracking in sync.',
    'description': """
Plennix Technologies — Custom Sale Order Management (JDE)
=========================================================

Connects the Transmed B2B web shop to JD Edwards (JDE). Confirmed orders are
sent to JDE, split into the delivery notes JDE creates, and kept up to date
every 10 minutes with JDE's order status, invoiced quantities, prices and
invoice number. Returns created in JDE are brought back into Odoo and, for cash
customers, refunded to their eWallet. Customers see JDE's prices and totals
and their expected delivery date, and can track their delivery on a map.

Key Features
------------
* Confirmed web orders are created in JDE automatically and split per JDE delivery note
* JDE order status, delivered quantities, prices, taxes, delivery charge and invoice number synced every 10 minutes
* Deliveries validated automatically when JDE prints the invoice
* JDE returns (GRV) created in Odoo, and cash customers refunded to their eWallet
* Expected delivery date on checkout, following the customer's delivery days in KSA
* Sliced / shredded options and number of pieces for ARP products on the web shop
* Live delivery tracking (driver, vehicle, map) from the customer portal
* Product brands

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
        'sale',
        'sale_stock',
        'stock',
        'stock_delivery',
        'website',
        'website_sale',
        'website_sale_loyalty',
        'loyalty',
        'integration_log',
        'customer_create_api',
        'checkavailability_integration_jde',
        'payment_hyperpay_extended',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_action_saleorder_status.xml',
        'data/scheduler_action_order_return.xml',
        'data/loyalty_program_data.xml',
        'views/custom_checkout_template.xml',
        'views/custom_sale_order_view.xml',
        'views/stock_picking_inherit_view.xml',
        'views/product_template_website_inherit.xml',
        'views/sale_order_line_inherit.xml',
        'views/sale_order_portal_views.xml',
        'views/res_config_setting_inherit.xml',
        'views/track_order.xml',
        'views/product_brand.xml',
        'views/quotation_report.xml',
        'views/loyalty_card_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_saleorder_management/static/src/css/tracking_order.css',
            'custom_saleorder_management/static/src/js/custom_website_sale.js',
            'custom_saleorder_management/static/src/js/tracking_order.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
