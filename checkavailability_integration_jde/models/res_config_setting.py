import requests

from odoo import fields, models


class ResConfigSettingsJDE(models.TransientModel):
    _inherit = 'res.config.settings'

    jde_token_request_url = fields.Char("JDE Request Url", readonly=False,
                                        related="company_id.jde_token_request_url")
    jde_request_username = fields.Char("JDE Request UserName", readonly=False,
                                       related="company_id.jde_request_username")
    jde_request_password = fields.Char("JDE Request Password", readonly=False,
                                       related="company_id.jde_request_password")
    jde_request_env = fields.Char("JDE Environment", readonly=False, related="company_id.jde_request_env")
    jde_request_role = fields.Char("JDE Role", readonly=False, related="company_id.jde_request_role")
    jde_checkavailability_url = fields.Char("JDE Availability Url", readonly=False,
                                            related="company_id.jde_checkavailability_url")
    jde_bulk_update_url = fields.Char("JDE Bulk Update Url", readonly=False, related="company_id.jde_bulk_update_url")
    jde_logout_url = fields.Char("JDE Logout Url", readonly=False, related="company_id.jde_logout_url")
    jde_last_integration_timestamp = fields.Datetime(
        related='company_id.jde_last_integration_timestamp',
        readonly=False,
        string="Last JDE Integration Timestamp"
    )

    def get_jde_token(self):
        """ "Connect" button: test the company's JDE credentials. """
        self.ensure_one()
        company = self.company_id
        error = self.env._("JDE did not return a token. Check the integration log.")
        try:
            token = company.get_jde_token()
        except requests.exceptions.RequestException as e:
            token = False
            error = self.env._("Could not reach JDE: %s", e)
        except (ValueError, KeyError):
            token = False
        if token:
            company.jde_logout(token)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success' if token else 'danger',
                'message': self.env._("Connected to JDE.") if token else error,
                'sticky': False,
            },
        }
