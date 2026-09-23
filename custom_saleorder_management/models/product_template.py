from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Also defined in product_create_api, which depends on this module; defined here
    # because the JDE order sync and the product page rely on them.
    jde_product_id = fields.Char("jde_product_id")
    item_type = fields.Char("Item Type")
