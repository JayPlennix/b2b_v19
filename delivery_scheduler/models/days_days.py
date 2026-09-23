from odoo import fields, models


class DayDay(models.Model):
    _name = 'days.days'
    _description = 'Days'

    name = fields.Char(string='Name', required=True)
