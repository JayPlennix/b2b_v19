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
import base64
from collections import OrderedDict

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools.image import image_process
from odoo.tools.translate import _

from odoo.addons.portal.controllers.portal import CustomerPortal


class ReturnCustomerPortal(CustomerPortal):
    """Portal pages for the customer return orders"""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'return_count' in counters:
            values['return_count'] = request.env['sale.return'].search_count(
                self._b2b_return_domain()) if request.env['sale.return'].has_access('read') else 0
        return values

    def _b2b_return_domain(self):
        """Returns the current user placed, or of their company."""
        partner = request.env.user.partner_id
        return ['|', ('user_id', '=', request.env.user.id),
                ('partner_id', 'child_of', [partner.commercial_partner_id.id])]

    @http.route(['/my/return_orders', '/my/return_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_sale_return(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """List of the customer return orders"""
        values = self._prepare_portal_layout_values()
        sale_return = request.env['sale.return']
        domain = self._b2b_return_domain()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'sale': {'label': _('Sale Order'), 'order': 'sale_order'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'confirm', 'done', 'cancel'])]},
            'confirm': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirm')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        return_count = sale_return.search_count(domain)
        pager = request.website.pager(
            url="/my/return_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=return_count, page=page, step=self._items_per_page)
        orders = sale_return.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_return_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'Sale_Return',
            'default_url': '/my/return_orders',
            'pager': pager,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("website_return_management.portal_my_returns", values)

    @http.route(['/my/return_orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_return_detail(self, order_id=None, access_token=None, report_type=None, download=False, **kw):
        """Return order details"""
        try:
            order_sudo = self._document_check_access('sale.return', order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='website_return_management.report_sale_returns', download=download)
        values = self._sale_return_get_page_view_values(order_sudo, access_token, **kw)
        return request.render("website_return_management.portal_sale_return_page", values)

    def _sale_return_get_page_view_values(self, order, access_token, **kwargs):
        def resize_to_48(b64source):
            if not b64source:
                b64source = request.env['ir.binary']._placeholder()
            else:
                b64source = base64.b64decode(b64source)
            return base64.b64encode(image_process(b64source, size=(48, 48)))

        values = {'orders': order, 'resize_to_48': resize_to_48}
        return self._get_page_view_values(order, access_token, values, 'my_return_history', False, **kwargs)
