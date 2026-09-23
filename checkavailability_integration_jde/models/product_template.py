import logging
from datetime import datetime, timedelta

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 120


class ProductCheckavailability(models.Model):
    _inherit = "product.template"

    # Also defined in custom_saleorder_management / product_create_api, which depend on this module.
    jde_product_id = fields.Char("jde_product_id")
    jde_stock_location = fields.Many2one('stock.location', string="JDE Stock Location")
    timestamp_jde = fields.Datetime("Timestamp_jde")

    def _parse_jde_timestamp(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.strptime(value.split(' :')[0], '%Y-%m-%d')

    def update_quantity_bulk_api(self):
        for company in self.env['res.company'].sudo().search([]):
            if company.jde_bulk_update_url and company.dta_schemaname and company.jde_logout_url:
                checkavailability_bulk_url = company.jde_bulk_update_url
                auth_token = company.get_jde_token()
                dta_schemaname = company.dta_schemaname

                last_timestamp_dt = company.jde_last_integration_timestamp or (datetime.now() - timedelta(days=1))
                last_timestamp_str = last_timestamp_dt.strftime("%m/%d/%Y %H:%M:%S")

                payload = {
                    "token": auth_token,
                    "DTA_SchemaName": dta_schemaname or "CRPDTA",
                    "LASTINTEGRATIONTIMESTAMP": last_timestamp_str
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                try:
                    response = requests.post(checkavailability_bulk_url, headers=headers, json=payload,
                                             timeout=JDE_REQUEST_TIMEOUT)
                    integration_record = self.env['integration.log'].sudo().create({
                        'name': 'JDE Update Bulk Quantity',
                        'url': str(checkavailability_bulk_url),
                        'headers': str(headers),
                        'payload': str(payload),
                    })
                    if response.status_code == 200:
                        integration_record.write({'response': str(response.json())})
                    elif response.status_code == 502:
                        integration_record.write({'response': str(response.text)})
                    else:
                        integration_record.write({'response': str(response.json())})
                    self.env.cr.commit()
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'rows' in response_data:
                            for product_item in response_data['rows']:
                                product_jde_id = product_item.get("SKU").strip()
                                lot_product_data = product_jde_id
                                if '.' in str(product_jde_id) and company.is_ksa:
                                    lot_product_data = int(str(product_jde_id).split('.')[0])

                                product_tmpl_id = self.env['product.template'].search(
                                    [('jde_product_id', '=', lot_product_data)], limit=1)
                                if product_tmpl_id:
                                    _logger.debug("JDE bulk quantity row: %s", product_item)
                                    if product_item.get("TIMESTAMP"):
                                        timestamp = self._parse_jde_timestamp(product_item.get("TIMESTAMP"))
                                        product_tmpl_id.timestamp_jde = timestamp
                                        company.jde_last_integration_timestamp = timestamp
                                    product_product_id = self.env['product.product'].search(
                                        [("product_tmpl_id", '=', product_tmpl_id.id)], limit=1)
                                    self.update_stock_bulk_quantities(product_item, product_product_id, company)
                        _logger.info("***Update Bulk Quantity JDE Successfully***")
                        company.jde_logout(auth_token)
                except requests.exceptions.RequestException as e:
                    _logger.error("Error Bulk updating JDE quantities: %s", e)

    def update_stock_bulk_quantities(self, product_item, product_product_id, company):
        try:
            expiry_date = datetime.strptime(product_item.get("EXPIRY"), '%d/%m/%Y').date()
        except ValueError:
            return

        sku = product_item.get("SKU").strip()
        quantity = float(product_item.get("QTYAVAILABLE_S"))
        location = product_item.get('WHLOC')
        lot_name = sku
        if '.' in sku:
            lot_name = sku.split('.')[1]

        location_id = product_product_id.product_tmpl_id.jde_stock_location
        if company.is_ksa and location:
            location_id = self.env['stock.location'].sudo().search([("ksa_location", '=', location.lower())], limit=1)

            stock_quants = self.env['stock.quant'].sudo().search(
                [("product_id", '=', product_product_id.id), ('location_id', '=', location_id.id),
                 ('lot_id.name', '=', lot_name)])
            if stock_quants:
                for stock_quant in stock_quants:
                    if not stock_quant.lot_id or stock_quant.lot_id.ref == sku:
                        stock_quant.quantity = quantity + stock_quant.reserved_quantity
                        stock_quant.expiration_date = expiry_date
            else:
                lot_id = self.env['stock.lot'].sudo().search(
                    [("name", '=', lot_name), ('product_id', '=', product_product_id.id),
                     ('company_id', '=', product_product_id.company_id.id)], limit=1)
                if not lot_id:
                    lot_id = self.env['stock.lot'].create({
                        "name": lot_name,
                        "product_id": product_product_id.id,
                        "company_id": product_product_id.company_id.id,
                        "expiration_date": expiry_date,
                        "ref": sku,
                    })
                if location_id and quantity > 0.0:
                    self.env['stock.quant']._update_available_quantity(product_product_id, location_id, quantity,
                                                                       lot_id=lot_id or None)
        else:
            stock_quants = self.env['stock.quant'].sudo().search(
                [("product_id", '=', product_product_id.id), ('location_id', '=', location_id.id)])

            if stock_quants:
                for stock_quant in stock_quants:
                    if not stock_quant.lot_id or stock_quant.lot_id.ref == sku:
                        stock_quant.quantity = quantity + stock_quant.reserved_quantity
                        stock_quant.expiration_date = expiry_date
            else:
                lot_id = self.env['stock.lot'].sudo().search([("ref", '=', sku)], limit=1)
                if location_id and quantity > 0.0:
                    self.env['stock.quant']._update_available_quantity(product_product_id, location_id, quantity,
                                                                       lot_id=lot_id or None)
        return
