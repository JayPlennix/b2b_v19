# -*- coding: utf-8 -*-
{
    'name': 'Custom Website (Transmed B2B)',
    'version': '19.0.1.0.1',
    'category': 'Website/Website',
    'summary': 'Transmed B2B web shop: category menu, per-kg prices, customer-specific catalogue, salesperson ordering and credit checkout.',
    'description': """
Plennix Technologies — Custom Website (Transmed B2B)
====================================================

Turns the Odoo web shop into Transmed's B2B ordering portal. Customers browse a
category mega menu, see prices per kilogram for products sold by the gram, and
only see the products meant for them (products reserved to specific customers,
and in KSA only what their warehouse stocks). Customers on credit terms confirm
orders without paying online, portal salespersons can place orders on behalf of
their customers, and customers follow their orders with the JD Edwards status.

Key Features
------------
* Category mega menu and mobile category menu
* Prices per kg for products sold by the gram
* Products reserved to specific customers; KSA catalogue limited to the customer's warehouse stock
* Specifications (item number, brand, origin, storage...) on the product page
* Salespersons order on behalf of their customers; credit customers confirm without online payment
* Order list with status, delivery JDE status, clear cart, logged-in-only wishlist
* Popular Brands, Main Categories, Featured Categories, Best Selling and High Review snippets

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'web', 'website', 'portal', 'auth_signup', 'digest', 'http_routing', 'mail', 'utm', 'payment',
        'social_media', 'google_recaptcha', 'im_livechat',
        'sale', 'sale_stock', 'product',
        'website_sale', 'website_sale_comparison', 'website_sale_wishlist', 'website_sale_stock_wishlist',
        'custom_saleorder_management', 'product_create_api',
    ],
    'data': [
        'security/ir_rule.xml',
        'data/best_selling_product.xml',
        'data/high_review_products.xml',
        'data/product_snippet_templates.xml',
        'data/featured_categories.xml',
        'data/featured_categories_template.xml',
        'views/backend_views.xml',
        'views/website_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_website/static/src/css/product_page.css',
            'custom_website/static/src/css/home_page.css',
            'custom_website/static/src/css/website_footer.css',
            'custom_website/static/src/js/clear_cart.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
