import logging
from datetime import datetime

import requests

from odoo import Command, fields, models

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 60


class DeliveryScheduler(models.Model):
    _name = 'delivery.scheduler'
    _description = 'Delivery Scheduler'

    customer_id = fields.Many2one('res.partner', string="Customer")
    effective_date = fields.Date(string="Effective Date")
    delivery_udc = fields.Char(string="Delivery UDC")
    delivery_days = fields.Integer(string="Number of Delivery Days")
    day_ids = fields.Many2many('days.days', string='Delivery Days')
    expiry_date = fields.Date(string="Expiry Date")

    def update_delivery_scheduler_api(self):
        for company in self.env['res.company'].sudo().search([]):
            if company.delivery_scheduler_url and company.dta_schemaname:
                auth_token = company.get_jde_token()
                dta_schemaname = company.dta_schemaname
                delivery_scheduler_url = company.delivery_scheduler_url
                payload = {
                    "token": auth_token,
                    "DTA_SchemaName": dta_schemaname or "CRPDTA",
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                try:
                    response = requests.post(delivery_scheduler_url, headers=headers, json=payload,
                                             timeout=JDE_REQUEST_TIMEOUT)
                    integration_obj = self.env['integration.log'].sudo()
                    integration_record = integration_obj.create({
                        'name': 'JDE Delivery Scheduler',
                        'url': str(delivery_scheduler_url),
                        'headers': str(headers),
                        'payload': str(payload),
                    })
                    if response.status_code == 200:
                        integration_record.sudo().write({
                            'response': str(response.json()),
                        })
                    else:
                        integration_record.sudo().write({
                            'response': str(response.text),
                        })
                    self.env.cr.commit()

                    if response.status_code == 200:
                        response_data = response.json()

                        for jde_data in response_data["rows"]:
                            customer_id = jde_data.get('CUSTOMER_ID').strip()
                            effective_date = jde_data.get('EFFECTIVE_DATE').strip()
                            delivery_udc = jde_data.get('DELIVERY_UDC').strip()
                            delivery_days = jde_data.get('DELIVERY_DAYS').strip()
                            expiry_date = jde_data.get('EXPIRY_DATE').strip()

                            effective_da = False
                            if effective_date and effective_date != 'null':
                                effective_da = datetime.strptime(effective_date, "%d/%m/%Y")

                            delivery_day = []
                            if delivery_days:
                                if ',' in delivery_days:
                                    days = delivery_days.split(',')
                                    delivery_day = self.env['days.days'].sudo().search([('name', 'in', days)]).ids
                                else:
                                    delivery_day = self.env['days.days'].sudo().search(
                                        [('name', '=', delivery_days)]).ids

                            expiry_da = False
                            if expiry_date and expiry_date != 'null':
                                expiry_da = datetime.strptime(expiry_date, "%d/%m/%Y")

                            partner = self.env['res.partner'].sudo().search([('b2b_customer_id', '=', customer_id)],
                                                                            limit=1)

                            delivery_scheduler = self.env['delivery.scheduler'].sudo().search(
                                [('customer_id', 'in', partner.ids)], limit=1)
                            if partner:
                                vals = {
                                    'customer_id': partner.id,
                                    'delivery_udc': delivery_udc,
                                    'day_ids': [Command.link(day) for day in delivery_day],
                                    'expiry_date': expiry_da,
                                    'effective_date': effective_da,
                                }
                                if delivery_scheduler:
                                    delivery_scheduler.sudo().write(vals)
                                else:
                                    delivery_scheduler.sudo().create(vals)

                        payload_logout = {"token": auth_token}
                        logout_url = company.jde_logout_url
                        requests.post(logout_url, headers=headers, json=payload_logout,
                                      timeout=JDE_REQUEST_TIMEOUT)
                except requests.exceptions.RequestException as e:
                    _logger.error("Error Delivery Scheduler JDE: %s", e)
