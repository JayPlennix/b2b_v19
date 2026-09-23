from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class SaleOrderTracking(CustomerPortal):

    @http.route('/tracking_sale_order', type='jsonrpc', auth="public", methods=['POST'])
    def tracking_sale_order(self, sale_order_id, access_token=None):
        # Same access rule as the order's portal page: the customer, or a valid access token.
        try:
            sale_order = self._document_check_access('sale.order', sale_order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'redirect': False, 'url': '/my'}

        order_picking = request.env['stock.picking'].sudo().search(
            [('origin', '=', sale_order.name), ('picking_type_id.code', '=', 'outgoing'),
             ('jde_state', '=', 'invoice_printed')], limit=1)
        if order_picking:
            sale_order._order_tracking_api(sale_order, order_picking)

        if (order_picking and order_picking.asset_latitude and order_picking.asset_longitude
                and order_picking.customer_latitude and order_picking.customer_longitude):
            google_maps_url = (f"https://www.google.com/maps/dir/?api=1"
                               f"&origin={order_picking.asset_latitude},{order_picking.asset_longitude}"
                               f"&destination={order_picking.customer_latitude},{order_picking.customer_longitude}")
            return {'redirect': True, 'url': google_maps_url, 'driver': order_picking.driver,
                    'vehicle': order_picking.vehicle}
        return_url = request.httprequest.host_url + sale_order.get_portal_url()
        return {'redirect': False, 'url': return_url}
