from odoo import Command, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_child_transaction(self, amount, is_refund=False, **custom_create_values):
        # Keep captures, voids and refunds of web shop payments linked to their sales order.
        if self._is_hyperpay() and self.sale_order_ids and 'sale_order_ids' not in custom_create_values:
            custom_create_values['sale_order_ids'] = [Command.set(self.sale_order_ids.ids)]
        return super()._create_child_transaction(amount, is_refund=is_refund, **custom_create_values)
