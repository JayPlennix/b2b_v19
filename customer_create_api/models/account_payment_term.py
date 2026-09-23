from odoo import fields, models


class PaymentTermb2b(models.Model):
    _inherit = "account.payment.term"

    b2b_code = fields.Char(string='B2B Code')
    is_cash_payment_term = fields.Boolean(string="IS Cash Payment Term")
