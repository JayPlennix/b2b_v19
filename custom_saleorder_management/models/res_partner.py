from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Also defined in custom_website, which depends on this module.
    customer_location_id = fields.Many2one('stock.location', string="Customer Location")
