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
from datetime import datetime

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class WebsiteSaleReturn(CustomerPortal):

    @http.route('/sale_return', type='http', methods=['POST'], auth="user", website=True)
    def sale_return(self, **kwargs):
        """Create a return order for one line of one of the customer's orders."""
        try:
            order_sudo = self._document_check_access('sale.order', int(kwargs.get('order_id') or 0),
                                                     kwargs.get('access_token'))
        except (AccessError, MissingError):
            return request.redirect('/my')

        # A share link (access token) is not enough to file a return: the order must belong to
        # the customer's own company.
        partner = request.env.user.partner_id
        if order_sudo.partner_id.commercial_partner_id != partner.commercial_partner_id:
            raise Forbidden()

        order_line_sudo = order_sudo.order_line.filtered(lambda l: l.id == int(kwargs.get('product') or 0))
        quantity = float(kwargs.get('qty') or 0)
        if not order_line_sudo or quantity <= 0 or quantity > order_line_sudo.remaining_qty_return:
            raise Forbidden()

        reason_id = int(kwargs['reason_id']) if kwargs.get('reason_id') else False
        values = {
            'partner_id': order_sudo.partner_id.id,
            'sale_order': order_sudo.id,
            'sale_order_line': order_line_sudo.id,
            'product_id': order_line_sudo.product_id.id,
            'quantity': quantity,
            'reason_id': reason_id,
            'user_id': request.env.uid,
            'create_date': datetime.now(),
            'state': 'draft',
            'return_from': 'GS',
        }
        stock_picks = request.env['stock.picking'].sudo().search([('origin', '=', order_sudo.name)])
        moves = stock_picks.move_ids.filtered(lambda p: p.product_id == order_line_sudo.product_id)
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            return_order = request.env['sale.return'].sudo().create(values)
            moves[0].picking_id.sudo().write({'return_order': return_order.id, 'return_order_picking': False})
        return request.redirect('/my/request-thank-you')

    @http.route('/my/request-thank-you', type='http', website=True, auth='public')
    def maintenance_request_thanks(self):
        return request.render('website_return_management.customers_request_thank_page')
