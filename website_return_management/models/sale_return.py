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
from odoo import api, fields, models


class ReturnOrder(models.Model):
    """Class for sale order return"""
    _name = 'sale.return'
    _inherit = ['portal.mixin']
    _rec_name = "name"
    _order = "name"
    _description = "Return Order"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('sale.return')

    active = fields.Boolean('Active', default=True, help='Is active or not')
    name = fields.Char(string="Name", default=_get_default_name, help='Name of return order')
    product_id = fields.Many2one('product.product', string="Product Variant", required=True,
                                 help="Product variant that needs to be returned")
    product_tmpl_id = fields.Many2one('product.template', related="product_id.product_tmpl_id", store=True,
                                      string="Product", help='Return Product')
    sale_order = fields.Many2one('sale.order', string="Sale Order", required=True, help='Reference of Sale Order')
    sale_order_line = fields.Many2one('sale.order.line', string="Sale Order Line", required=True,
                                      help='Reference of the Sale Order line')
    partner_id = fields.Many2one('res.partner', string="Customer", help='Customer of the return order')
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user,
                              help='Responsible user for the return order')
    quantity = fields.Float(string="Quantity", default=0, help='Return quantity')
    received_qty = fields.Float(string="Received Quantity", help='Received item quantity')
    reason_id = fields.Many2one('return.reason', string="Reason")
    reason = fields.Char(string="Reason Description", compute="_compute_reason", store=True)
    code = fields.Char(related='reason_id.code', string="Code", store=True)
    unit_price = fields.Float(string="Unit Price", compute="_compute_unit_price", store=True)
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    stock_picking = fields.One2many('stock.picking', 'return_order_pick', domain="[('return_order', '=', False)]",
                                    string="Return Picking",
                                    help="Return picking of the corresponding return order")
    picking_count = fields.Integer(compute="_compute_delivery", string='Picking Order', copy=False, default=0,
                                   store=True, help='Picking count of the return')
    delivery_count = fields.Integer(compute="_compute_delivery", string='Delivery Order', copy=False, default=0,
                                    store=True, help='Delivery count of the return')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Canceled')],
                             string='Status', readonly=True, default='draft', help='Status of return order')
    source_pick = fields.One2many('stock.picking', 'return_order', string="Source Delivery",
                                  domain="[('return_order_pick', '=', False)]",
                                  help="Delivery orders of the corresponding return order")
    note = fields.Text("Note")
    to_refund = fields.Boolean(string='Update SO/PO Quantity',
                               help='Trigger a decrease of the delivered/received quantity in the associated '
                                    'Sale Order/Purchase Order')
    return_from = fields.Selection([('GS', 'GS'), ('SR', 'SR')], string='Return From', default='SR', readonly=True,
                                   help='Where the return comes from')

    @api.depends('sale_order_line')
    def _compute_unit_price(self):
        for rec in self:
            rec.unit_price = rec.sale_order_line.price_unit if rec.sale_order_line else 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.unit_price

    @api.depends('reason_id')
    def _compute_reason(self):
        for rec in self:
            rec.reason = rec.reason_id.name

    def return_confirm(self):
        """Confirm the sale return: create the return picking and notify the salesperson."""
        self.ensure_one()
        if not self.source_pick:
            stock_picks = self.env['stock.picking'].search([('origin', '=', self.sale_order.name)])
            moves = stock_picks.move_ids.filtered(lambda p: p.product_id == self.product_id)
        else:
            moves = self.source_pick.move_ids.filtered(lambda p: p.product_id == self.product_id)
        if not moves:
            return
        moves = moves.sorted('product_uom_qty', reverse=True)
        return_pick_wizard = self.env['stock.return.picking'].create({'picking_id': moves[0].picking_id.id})
        return_pick_wizard.product_return_moves.unlink()
        self.env['stock.return.picking.line'].create({
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'wizard_id': return_pick_wizard.id,
            'move_id': moves[0].id,
            'to_refund': self.to_refund,
        })
        return_pick = return_pick_wizard._create_return()
        if return_pick:
            return_pick.update({'note': self.reason})
            return_pick.write({'return_order': False, 'return_order_pick': self.id, 'return_order_picking': True})
            self.env.ref('website_return_management.mail_template_return_order_notify').send_mail(
                self.id, force_send=True)
            self.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        for rec in self.stock_picking.filtered(lambda s: s.state not in ['done', 'cancel']):
            rec.action_cancel()

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Sale Return - %s' % self.name

    def _compute_access_url(self):
        super()._compute_access_url()
        for order in self:
            order.access_url = '/my/return_orders/%s' % order.id

    @api.depends('stock_picking', 'source_pick', 'state')
    def _compute_delivery(self):
        """Compute the picking and delivery counts"""
        for rec in self:
            rec.delivery_count = len(rec.source_pick) or self.env['stock.picking'].search_count(
                [('return_order', '=', rec.id), ('return_order_picking', '=', False)])
            rec.picking_count = len(rec.stock_picking) or self.env['stock.picking'].search_count(
                [('return_order_pick', '=', rec.id), ('return_order_picking', '=', True)])

    def _action_view_pickings(self, pickings):
        """Open one or several transfers."""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        picking = pickings.filtered(lambda p: p.picking_type_id.code == 'outgoing')[:1] or pickings[:1]
        action['context'] = dict(
            self.env.context, default_partner_id=self.partner_id.id,
            default_picking_type_id=picking.picking_type_id.id)
        return action

    def action_view_picking(self):
        """View the return transfers"""
        self.ensure_one()
        pickings = self.stock_picking or self.env['stock.picking'].search(
            [('return_order_pick', '=', self.id), ('return_order_picking', '=', True)])
        return self._action_view_pickings(pickings)

    def action_view_delivery(self):
        """View the delivery transfers"""
        self.ensure_one()
        pickings = self.source_pick or self.env['stock.picking'].search(
            [('return_order', '=', self.id), ('return_order_picking', '=', False)])
        return self._action_view_pickings(pickings)

    @api.onchange('sale_order', 'source_pick')
    def onchange_sale_order(self):
        """All the fields are updated according to the sale order"""
        delivery = self.env['stock.picking']
        if self.sale_order:
            self.partner_id = self.sale_order.partner_id
            delivery = self.env['stock.picking'].search([('origin', '=', self.sale_order.name)])
        if self.source_pick:
            delivery = self.source_pick
        product_ids = delivery.move_ids.product_id.ids if delivery else self.sale_order.order_line.product_id.ids
        return {'domain': {'source_pick': [('id', 'in', delivery.ids)], 'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('product_id')
    def onchange_product_id(self):
        """Compute the received quantity"""
        if self.product_id and self.source_pick:
            moves = self.source_pick.move_ids.filtered(lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity'))

    def get_portal_url1(self):
        """Return the portal URL of this return order."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/my/return_orders/{self.id}"
