from collections import defaultdict

from odoo import fields, models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    actual_name = fields.Char(
        string="Actual Name",
        help="Name shown to customers on the web shop instead of the internal product name.")

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        res = super()._get_additionnal_combination_info(product_or_template, quantity, uom, date, website)
        product_or_template = product_or_template.sudo()
        if product_or_template.is_product_variant:
            res['cart_lines'] = product_or_template._get_cart_lines(website)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_cart_lines(self, website=None):
        """ Quantities of this product already in the cart, per unit of measure. """
        if self.allow_out_of_stock_order:
            return []
        cart = request.cart if request and hasattr(request, 'cart') else None
        if not cart:
            return []
        grouped_lines = defaultdict(float)
        for line in cart.order_line.filtered(lambda l: l.product_id == self):
            grouped_lines[line.product_uom_id.name] += line.product_uom_qty
        return [{'qty': qty, 'uom': uom} for uom, qty in grouped_lines.items()]
