# -*- coding: utf-8 -*-

from odoo import fields, models


class Productb2b(models.Model):
    _inherit = "product.template"

    storage = fields.Char("Storage")
    temperature = fields.Char("Temperature")
    jde_product_id = fields.Char("jde_product_id")
    jde_product_name = fields.Char(string="JDE Product Name")
    timestamp_jde = fields.Datetime("Timestamp_jde")
    product_family = fields.Char("Product Family")
    product_family_name = fields.Char("Product Family Name")
    item_type = fields.Char("Item Type")
    item_type_name = fields.Char("Item Type Name")
    short_item_no = fields.Integer("Short Item No")
    brand_id = fields.Many2one('product.brand', string="Odoo Brand")
    brand = fields.Char("Brand")
    brand_name = fields.Char("Brand Name")
    brand_type = fields.Char("Brand Type")
    brand_type_name = fields.Char("Brand Type Name")
    supplier_code = fields.Char("Supplier Code")
    supplier_name = fields.Char("Supplier Name")
    check_availability = fields.Boolean("Check Availability")
    create_via_api = fields.Boolean("create_via_api")
    jde_stock_location = fields.Many2one('stock.location', string="JDE Stock Location")
    product_selling_type = fields.Selection([('sliced', 'SLICED'), ('shredded', 'SHREDDED')],
                                            string="Product Selling Types", default='sliced')

    def _get_default_category_id(self):
        return self.env['product.category'].sudo().search([], limit=1).id

    categ_id = fields.Many2one(default=_get_default_category_id, required=True)
