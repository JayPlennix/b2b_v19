from odoo import models


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    def _get_available_tokens(self, providers_ids, partner_id, is_validation=False, **kwargs):
        # HyperPay / Apple Pay tokens created in 17.0 only hold the pre-authorization of one order:
        # never offer them as saved payment methods.
        tokens = super()._get_available_tokens(providers_ids, partner_id, is_validation=is_validation, **kwargs)
        hyperpay_codes = self.env['payment.provider']._hyperpay_provider_codes()
        return tokens.filtered(lambda token: token.provider_code not in hyperpay_codes)
