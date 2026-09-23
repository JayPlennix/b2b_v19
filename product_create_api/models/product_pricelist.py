from odoo import fields, models


class ProductPriceList(models.Model):
    _inherit = "product.pricelist"

    F4101_timestamp = fields.Datetime("Timestamp_F4101")
    F4106_timestamp = fields.Datetime("Timestamp_F4106")
    timestamp_jde = fields.Datetime("Timestamp_jde")
