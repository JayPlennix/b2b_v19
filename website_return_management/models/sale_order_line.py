# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#    Odoo 19.0 migration: Plennix Technologies (https://www.plennix.com)
#
#    This program is free software: you can modify it under the terms of the GNU
#    AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
################################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Class for inherit sale order line"""
    _inherit = 'sale.order.line'

    remaining_qty_return = fields.Float(string="Remaining Qty Return", compute="_compute_remaining_qty_return",
                                        store=True)

    @api.depends('qty_delivered', 'qty_delivered_method',
                 'analytic_line_ids.so_line', 'analytic_line_ids.unit_amount', 'analytic_line_ids.product_uom_id')
    def _compute_remaining_qty_return(self):
        SaleReturn = self.env['sale.return']
        for line in self:
            lines_same_product = line.order_id.order_line.filtered(lambda l: l.product_id == line.product_id)
            delivered_qty = sum(lines_same_product.mapped('qty_delivered'))
            returns = SaleReturn.sudo().search([
                ('sale_order', '=', line.order_id.id),
                ('product_id', '=', line.product_id.id),
                ('state', 'in', ['draft', 'confirm', 'done']),
            ])
            total_returned = sum(returns.mapped('quantity'))
            line.remaining_qty_return = max(delivered_qty - total_returned, 0)
