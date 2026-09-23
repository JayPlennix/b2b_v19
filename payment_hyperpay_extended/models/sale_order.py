import logging

from odoo import Command, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Pre-authorization of orders paid in 17.0 (the HyperPay payment id is in `payment_details`).
    payment_token_id = fields.Many2one('payment.token', string='Token', copy=False)
    payment_done = fields.Boolean('Payment Done', copy=False)

    def _get_hyperpay_amount_to_capture(self):
        """ The customer pays the amount invoiced by JDE (eWallet already deducted).

        `jde_amount_total` comes from custom_saleorder_management, which depends on this module.
        """
        self.ensure_one()
        amount = self.jde_amount_total if 'jde_amount_total' in self._fields else self.amount_total
        return self.currency_id.round(amount)

    def recuring_payment(self):
        """ Capture the web shop payment once JDE has invoiced all deliveries.

        Called by custom_saleorder_management. The order's HyperPay / Apple Pay payment was
        pre-authorized at checkout; the amount invoiced by JDE is captured now and Odoo posts the
        payment.
        """
        for order in self:
            if order.payment_done:
                continue
            amount = order._get_hyperpay_amount_to_capture()
            if amount <= 0:
                continue
            authorized_tx = order.transaction_ids.filtered(
                lambda tx: tx.state == 'authorized' and not tx.source_transaction_id and tx._is_hyperpay()
            )[:1]
            try:
                if authorized_tx:
                    if authorized_tx.child_transaction_ids.filtered(lambda tx: tx.state in ('draft', 'pending')):
                        continue  # A capture is already in progress.
                    capture_tx = authorized_tx._capture(amount_to_capture=amount)
                    if capture_tx.state == 'done':
                        order.payment_done = True
                    else:
                        _logger.warning("HyperPay capture %s for %s ended in state %s: %s", capture_tx.reference,
                                        order.name, capture_tx.state, capture_tx.state_message)
                elif order.payment_token_id:
                    order._legacy_capture_payment(amount)
            except (UserError, ValidationError) as error:
                _logger.error("Error capturing the payment of %s: %s", order.name, error)

    def _legacy_capture_payment(self, amount):
        """ Capture an order pre-authorized in 17.0, before the migration. """
        self.ensure_one()
        token = self.payment_token_id
        source_tx = token.transaction_ids[:1]
        provider = source_tx.provider_id or token.provider_id
        entity_id = source_tx.hyperpay_entity_id or provider._hyperpay_get_entity_id(source_tx.payment_method_id)
        response = provider._hyperpay_make_request(f'/v1/payments/{token.payment_details}', {
            'entityId': entity_id,
            'paymentType': 'CP',
            'amount': '%.2f' % amount,
            'currency': source_tx.currency_id.name or self.currency_id.name,
        })
        capture_tx = self.env['payment.transaction'].sudo().create({
            'provider_id': provider.id,
            'payment_method_id': source_tx.payment_method_id.id or token.payment_method_id.id,
            'reference': self.env['payment.transaction']._compute_reference(
                provider.code, prefix=f'{self.name}-CP'),
            'sale_order_ids': [Command.set(self.ids)],
            'partner_id': source_tx.partner_id.id or self.partner_invoice_id.id,
            'amount': amount,
            'currency_id': source_tx.currency_id.id or self.currency_id.id,
            'token_id': token.id,
            'operation': 'offline',
            'hyperpay_entity_id': entity_id,
        })
        capture_tx._process(provider.code, response)
        if capture_tx.state == 'done':
            capture_tx._post_process()
            self.payment_done = True
