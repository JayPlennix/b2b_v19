from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Also defined in custom_saleorder_management, which this module depends on.
    customer_location_id = fields.Many2one('stock.location', string="Customer Location")
    is_ksa = fields.Boolean(string='Is Transmed KSA', related="company_id.is_ksa", store=True)
    is_jordan = fields.Boolean(string='Is Transmed Jordan', related="company_id.is_jordan", store=True)
