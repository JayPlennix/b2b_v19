from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    item_type = fields.Selection([('sliced', 'SLICED'), ('shredded', 'SHREDDED')], string="Item Type")
    sl_no_comp = fields.Integer('SNO.', compute="get_sl_no_comp", store=True)
    jde_line_tax_rate = fields.Integer('LINE TAX RATE')
    jde_price_total = fields.Monetary(string="JDE Total")
    jde_delivery_charge = fields.Monetary(string="Delivery Charge")
    jde_price_unit = fields.Monetary(string="JDE Price Unit")

    @api.depends('order_id', 'order_id.order_line')
    def get_sl_no_comp(self):
        for rec in self:
            for i, line in enumerate(rec.order_id.order_line):
                line.sl_no_comp = i + 1

    def _get_jde_quantity_and_uom(self):
        """ Quantity and unit sent to JDE. Packaging units (product.uom_ids) are
        converted to the product's unit, which is what JDE knows. """
        self.ensure_one()
        product = self.product_id
        if self.product_uom_id and self.product_uom_id in product.uom_ids:
            return self.product_uom_id._compute_quantity(self.product_uom_qty, product.uom_id), product.uom_id
        return self.product_uom_qty, self.product_uom_id
