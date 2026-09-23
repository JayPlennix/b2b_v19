import logging
from datetime import datetime

import requests

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 30


class WebsiteSaleInherit(WebsiteSale):
    """ Refresh the stock of the products shown from JDE (product page, cart, checkout).
    The pages are rendered lazily, after these methods return, so they show the
    refreshed quantities. """

    @route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        res = super().product(product, category=category, pricelist=pricelist, **kwargs)
        self.update_product_jde_quantity(product)
        return res

    @route()
    def cart(self, id=None, access_token=None, revive_method='', **post):
        res = super().cart(id=id, access_token=access_token, revive_method=revive_method, **post)
        if order_sudo := request.cart:
            cart_product = order_sudo.order_line.mapped('product_template_id')
            if cart_product:
                self.update_product_jde_quantity(cart_product)
        return res

    @route()
    def shop_checkout(self, try_skip_step=None, **query_params):
        res = super().shop_checkout(try_skip_step=try_skip_step, **query_params)
        if order_sudo := request.cart:
            checkout_product = order_sudo.order_line.mapped('product_template_id')
            if checkout_product:
                self.update_product_jde_quantity(checkout_product)
        return res

    def get_product_list(self, product):
        product_list = []
        for i in product:
            product_id = request.env['product.product'].search([("product_tmpl_id", '=', i.id)], limit=1)
            lots_ids = request.env['stock.lot'].sudo().search([('ref', '=', i.jde_product_id),
                                                               ('product_id', '=', product_id.id)])
            if lots_ids:
                product_list.extend(lot.name for lot in lots_ids)
            product_list.append(i.jde_product_id)
        return product_list

    def update_stock_quantities(self, product_item, product_product):
        try:
            expiry_date = datetime.strptime(product_item.get("EXPIRY"), '%d/%m/%Y').date()
        except ValueError:
            return

        sku = product_item.get("SKU").strip()
        if 'QTYAVAILABLE_P' in product_item and product_item.get('QTYAVAILABLE_P'):
            quantity = float(product_item.get("QTYAVAILABLE_P"))
            stock_quants = request.env['stock.quant'].sudo().search([("product_id", '=', product_product.id)])

            if stock_quants:
                for stock_quant in stock_quants:
                    if not stock_quant.lot_id or stock_quant.lot_id.name == sku:
                        stock_quant.quantity = quantity
                        stock_quant.expiration_date = expiry_date
            else:
                location_id = product_product.product_tmpl_id.jde_stock_location
                lot_id = request.env['stock.lot'].sudo().search([("ref", '=', sku)], limit=1)
                if location_id and quantity > 0.0:
                    request.env['stock.quant'].sudo()._update_available_quantity(
                        product_product, location_id, quantity, lot_id=lot_id or None)

    def update_product_jde_quantity(self, product):
        company = request.env.company
        if not (company and company.jde_checkavailability_url):
            return
        company = company.sudo()
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            auth_token = company.get_jde_token()
            checkavailability_url = company.jde_checkavailability_url

            product_list = self.get_product_list(product)
            formatted_product = ",".join(f"'{sku}'" for sku in product_list)

            payload = {
                "token": auth_token,
                "DTA_SchemaName": company.dta_schemaname or "CRPDTA",
                "SKU": formatted_product
            }
            response = requests.post(checkavailability_url, headers=headers, json=payload,
                                     timeout=JDE_REQUEST_TIMEOUT)
            integration_record = request.env['integration.log'].sudo().create({
                'name': 'Update Jde Product Quantity Request',
                'url': str(checkavailability_url),
                'headers': str(headers),
                'payload': str(payload),
            })
            if response.status_code == 200:
                integration_record.write({'response': str(response.json())})
                request.env.cr.commit()
                response_data = response.json()
                if 'rows' in response_data:
                    for product_item in response_data.get('rows'):
                        product_jde_id = product_item.get("SKU").strip()

                        lot_product_data = product_jde_id
                        if '.' in str(product_jde_id) and company.is_ksa:
                            lot_product_data = int(str(product_jde_id).split('.')[0])

                        product_tmpl_id = request.env['product.template'].sudo().search(
                            [('jde_product_id', '=', lot_product_data)], limit=1)
                        product_product_id = request.env['product.product'].sudo().search(
                            [("product_tmpl_id", '=', product_tmpl_id.id)], limit=1)
                        self.update_stock_quantities(product_item, product_product_id)
                    _logger.info("***Update Quantity JDE Successfully***")
                company.jde_logout(auth_token)
            elif response.status_code == 502:
                integration_record.write({'response': str(response.text)})
            else:
                integration_record.write({'response': str(response.json())})
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            # JDE being slow or down must never break the shop pages.
            _logger.error("Error updating JDE quantities: %s", e)
