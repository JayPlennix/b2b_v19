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
################################################################################
from odoo import fields, models


class StockReturnPicking(models.TransientModel):
    """Class for inherit stock return picking"""
    _inherit = 'stock.return.picking'

    def _create_return(self):
        """Link the return picking to the return order it comes from."""
        new_picking = super()._create_return()
        if self.picking_id.return_order:
            new_picking.write({
                'return_order_picking': False,
                'return_order': False,
                'return_order_pick': self.picking_id.return_order.id,
                'grv_order_type': 'GS',
            })
            self.picking_id.return_order.write({'state': 'confirm'})
        return new_picking


class StockPicking(models.Model):
    """Class for inherit stock picking to add fields"""
    _inherit = 'stock.picking'

    return_order = fields.Many2one('sale.return', string='Return order',
                                   help="Return order of the current transfer")
    return_order_pick = fields.Many2one('sale.return', string='Return order Pick',
                                        help="Return order this return picking belongs to")
    return_order_picking = fields.Boolean(string='Return order picking',
                                          help="True on return pickings, False on the original deliveries")

    def button_validate(self):
        """Mark the return order done once all its pickings are done."""
        res = super().button_validate()
        for rec in self:
            if rec.return_order_pick and all(line.state == 'done' for line in rec.return_order_pick.stock_picking):
                rec.return_order_pick.write({'state': 'done'})
        return res
