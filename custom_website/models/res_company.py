from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Also defined in custom_saleorder_management / checkavailability_integration_jde.
    is_ksa = fields.Boolean(string='Is Transmed KSA')
    is_jordan = fields.Boolean(string='Is Transmed Jordan')
