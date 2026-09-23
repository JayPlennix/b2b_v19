from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    company_id = fields.Many2one(
        'res.company', string="Company", store=True,
        default=lambda self: self.env.company)
