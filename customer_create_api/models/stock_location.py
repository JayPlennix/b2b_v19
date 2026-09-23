# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    ksa_location = fields.Selection([('jeddah', 'Jeddah'), ('riyadh', 'Riyadh'), ('dammam', 'Dammam')],string="KSA Location")
    ksa_location_code = fields.Selection([('JEDCR', 'JEDCR'), ('RUHCR', 'RUHCR'), ('DAMCR', 'DAMCR')],string="KSA Location Code")