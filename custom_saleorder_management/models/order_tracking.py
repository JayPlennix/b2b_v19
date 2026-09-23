import logging

import requests

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrderTracking(models.Model):
    _inherit = 'sale.order'

    def _order_tracking_api(self, sale_order, order_picking):
        company = self.company_id
        sale_order_tracking_url = company.sale_order_tracking_url
        params = {
            "UserName": company.sale_order_tracking_username,
            "Password": company.sale_order_tracking_password,
            "Order_Number": order_picking.carrier_tracking_ref,
            "Order_Type": "SO",
            "Branch_Plant": "TMD_QOZ"
        }

        try:
            response = requests.get(sale_order_tracking_url, params=params, timeout=10)
            integration_record = self.env['integration.log'].sudo().create({
                'name': 'JDE Order Tracking API Request',
                'url': str(sale_order_tracking_url),
                'headers': str(params),
                'payload': str(params),
            })
            if response.status_code == 200:
                integration_record.write({'response': str(response.json())})
                data = response.json()
            elif response.status_code == 502:
                integration_record.write({'response': str(response.text)})
                data = []
            else:
                integration_record.write({'response': str(response.json())})
                data = response.json()
            self.env.cr.commit()
            if not data:
                _logger.error("API response is empty or invalid")
                return

            response_data = data[0]  # Assuming only one record is returned
            self._update_order_tracking_info(order_picking, response_data)

        except requests.exceptions.RequestException as e:
            _logger.error("Order tracking API request failed: %s", e)
        except (ValueError, KeyError) as e:
            _logger.error("Error processing the API response: %s", e)

    def _update_order_tracking_info(self, order_picking, response_data):
        if order_picking:
            order_picking.sudo().write({
                'order_type': response_data.get('Order Type'),
                'vehicle': response_data.get('VEHICLE'),
                'driver': response_data.get('Driver'),
                'asset_latitude': response_data.get('Asset_Latitude'),
                'asset_longitude': response_data.get('Asset_Longitude'),
                'customer_latitude': response_data.get('Customer_Latitude'),
                'customer_longitude': response_data.get('Customer_Longitude'),
            })
