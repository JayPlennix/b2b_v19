from odoo import models, fields, api


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    picking_id = fields.Many2one('stock.picking', string="Picking")
