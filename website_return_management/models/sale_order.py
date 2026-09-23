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
from odoo import fields, models


class SaleOrder(models.Model):
    """Class for inherit sale order"""
    _inherit = 'sale.order'

    return_order_count = fields.Integer(compute="_compute_returns", string='Return Orders',
                                        help='Count of return order')

    def _compute_returns(self):
        """Count the return orders of the sales order."""
        self.return_order_count = 0
        groups = self.env['sale.return'].sudo()._read_group(
            domain=[('sale_order', 'in', self.ids)], groupby=['sale_order'], aggregates=['__count'])
        for order, count in groups:
            if order in self:
                order.return_order_count += count

    def action_open_returns(self):
        """Display the return orders of this sales order."""
        action = self.env['ir.actions.act_window']._for_xml_id('website_return_management.action_sale_return')
        action['domain'] = [('sale_order', '=', self.id)]
        action['context'] = {'search_default_order': 1}
        return action
