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


class ResPartner(models.Model):
    """Inherited res partner for adding return order count"""
    _inherit = 'res.partner'

    return_order_count = fields.Integer(string='Return Orders', compute="_compute_returns",
                                        help="For getting the return order count")

    def _compute_returns(self):
        """Count the return orders of the partner and of its children."""
        self.return_order_count = 0
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        groups = self.env['sale.return'].sudo()._read_group(
            domain=[('partner_id', 'in', all_partners.ids)], groupby=['partner_id'], aggregates=['__count'])
        for partner, count in groups:
            while partner:
                if partner in self:
                    partner.return_order_count += count
                partner = partner.parent_id

    def action_open_returns(self):
        """Display the return orders of this customer."""
        action = self.env['ir.actions.act_window']._for_xml_id('website_return_management.action_sale_return')
        if self.is_company:
            action['domain'] = [('partner_id.commercial_partner_id', '=', self.id)]
        else:
            action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'search_default_customer': 1}
        return action
