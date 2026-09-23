from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id, name, origin,
                               company_id, values):
        vals = super()._get_stock_move_values(product_id, product_qty, product_uom, location_dest_id, name,
                                              origin, company_id, values)

        if values.get('sale_line_id', False):
            sale_line_id = self.env['sale.order.line'].sudo().browse(values['sale_line_id'])
            if sale_line_id.order_id and sale_line_id.order_id.company_id and sale_line_id.order_id.company_id.is_ksa:
                partner = sale_line_id.order_id.partner_id
                vals['location_id'] = partner.customer_location_id.id if partner else False

        return vals
