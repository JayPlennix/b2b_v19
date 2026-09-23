from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    source = fields.Char(string="Source")