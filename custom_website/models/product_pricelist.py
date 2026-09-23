from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_ksa = fields.Boolean(string='Is Transmed KSA', related="company_id.is_ksa", store=True)
    is_jordan = fields.Boolean(string='Is Transmed Jordan', related="company_id.is_jordan", store=True)


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_price(self, product, quantity, uom, date, currency=None, **kwargs):
        # Some callers pass no unit: price in the product's own unit instead of crashing.
        return super()._compute_price(product, quantity, uom or product.uom_id, date, currency=currency, **kwargs)
