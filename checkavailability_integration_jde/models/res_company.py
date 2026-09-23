import json
import logging

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 60


class ResCompany(models.Model):
    _inherit = "res.company"

    jde_token_request_url = fields.Char("JDE Request Url")
    jde_request_username = fields.Char("JDE Request UserName")
    jde_request_password = fields.Char("JDE Request Password")
    jde_request_env = fields.Char("JDE Environment")
    jde_request_role = fields.Char("JDE Role")
    jde_checkavailability_url = fields.Char("JDE Availability Url")
    jde_bulk_update_url = fields.Char("JDE Bulk Update Url")
    jde_logout_url = fields.Char("JDE Logout Url")
    jde_last_integration_timestamp = fields.Datetime("Last JDE Integration Timestamp")
    # Also defined in custom_saleorder_management, which depends on this module.
    dta_schemaname = fields.Char("DTA_SchemaName")
    is_ksa = fields.Boolean(string='Is Transmed KSA')

    def get_jde_token(self):
        self.ensure_one()
        url = self.jde_token_request_url
        payload = {
            "username": self.jde_request_username,
            "password": self.jde_request_password,
            "environment": self.jde_request_env,
            "role": self.jde_request_role
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=JDE_REQUEST_TIMEOUT)
        integration_record = self.env['integration.log'].sudo().create({
            'name': 'JDE API Token Request',
            'url': str(url),
            'headers': str(headers),
            # never store the JDE password in the log
            'payload': str(dict(payload, password='***')),
        })
        if response.status_code == 200:
            integration_record.write({'response': str(response.json())})
        elif response.status_code == 502:
            integration_record.write({'response': str(response.text)})
        else:
            integration_record.write({'response': str(response.json())})
        self.env.cr.commit()
        if response.status_code == 200:
            token = response.json()['userInfo'].get('token')
            if token is not None:
                return token
        return ''

    def jde_logout(self, auth_token):
        self.ensure_one()
        if self.jde_logout_url:
            requests.post(self.jde_logout_url, headers={'Content-Type': 'application/json'},
                          json={"token": auth_token}, timeout=JDE_REQUEST_TIMEOUT)
