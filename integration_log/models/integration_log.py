from odoo import fields, models


class IntegrationLog(models.Model):
    _name = 'integration.log'
    _description = 'Integration Log'
    _order = 'id desc'

    name = fields.Char(string="Name")
    url = fields.Char(string="URL")
    headers = fields.Char(string="Headers")
    payload = fields.Text(string="Payload")
    model = fields.Char(string="Model Name")
    res_id = fields.Char(string="Res Id")
    response = fields.Char(string="Response")
