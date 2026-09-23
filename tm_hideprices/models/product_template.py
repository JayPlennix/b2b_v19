from odoo import models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        # Prices are for customers only: do not expose them to visitors who are not logged in.
        res = super()._get_additionnal_combination_info(product_or_template, quantity, uom, date, website)
        if request and request.env.user._is_public():
            for key in ('price', 'list_price', 'compare_list_price', 'base_unit_price'):
                if key in res:
                    res[key] = 0.0
        return res
