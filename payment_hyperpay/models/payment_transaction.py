# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
#
#################################################################################
import re

from odoo import _, api, fields, models

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_hyperpay import const

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    hyperpay_checkout_id = fields.Char(
        string="HyperPay Checkout Id", groups='base.group_user', readonly=True,
        help="Unique COPYandPAY checkout id of the transaction.")
    hyperpay_entity_id = fields.Char(
        string="HyperPay Entity Id", groups='base.group_user', readonly=True,
        help="Entity id the payment was made with; captures, voids and refunds must use the same one.")

    def _is_hyperpay(self):
        return self.provider_code in self.provider_id._hyperpay_provider_codes()

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to redirect the customer to the HyperPay payment page. """
        if not self._is_hyperpay():
            return super()._get_specific_rendering_values(processing_values)
        return {
            'api_url': '/payment/hyperpay/checkout',
            'reference': self.reference,
            'access_token': payment_utils.generate_access_token(self.reference, self.amount),
        }

    def _hyperpay_get_payment_type(self):
        """ 'PA' (pre-authorization) when the provider captures manually, 'DB' (debit) otherwise. """
        return 'PA' if self.provider_id.capture_manually else 'DB'

    def _hyperpay_create_checkout(self):
        """ Create the COPYandPAY checkout of the transaction and return its id. """
        self.ensure_one()
        provider = self.provider_id
        partner = self.partner_id
        entity_id = provider._hyperpay_get_entity_id(self.payment_method_id)
        data = {
            'entityId': entity_id,
            'amount': '%.2f' % self.amount,
            'currency': self.currency_id.name,
            'paymentType': self._hyperpay_get_payment_type(),
            'merchantTransactionId': self.reference,
            'billing.street1': partner.street or '',
            'billing.street2': partner.street2 or '',
            'billing.city': partner.city or '',
            'billing.state': partner.state_id.name or '',
            'billing.postcode': partner.zip or '',
            'billing.country': partner.country_id.code or '',
            'customer.givenName': partner.name or '',
            'customer.surname': partner.name or '',
            'customer.email': partner.email or '',
            'customer.phone': partner.phone or '',
        }
        response = provider._hyperpay_make_request('/v1/checkouts', data)
        checkout_id = response.get('id')
        if not checkout_id:
            self._set_error(_(
                "HyperPay could not start the payment: %s", response.get('result', {}).get('description')
            ))
            return False
        self.write({'hyperpay_checkout_id': checkout_id, 'hyperpay_entity_id': entity_id})
        return checkout_id

    def _hyperpay_fetch_payment_result(self, resource_path):
        """ Fetch the result of the COPYandPAY checkout from HyperPay. """
        self.ensure_one()
        return self.provider_id._hyperpay_make_request(
            resource_path, {'entityId': self.hyperpay_entity_id}, method='GET')

    def _hyperpay_follow_up_request(self, payment_type, amount=None):
        """ Send a back-office operation (CP, RV, RF) on the source transaction and process it. """
        source_tx = self.source_transaction_id
        entity_id = source_tx.hyperpay_entity_id or self.provider_id._hyperpay_get_entity_id(
            source_tx.payment_method_id)
        data = {'entityId': entity_id, 'paymentType': payment_type}
        if amount is not None:
            data.update({'amount': '%.2f' % amount, 'currency': self.currency_id.name})
        self.hyperpay_entity_id = entity_id
        response = self.provider_id._hyperpay_make_request(
            f'/v1/payments/{source_tx.provider_reference}', data)
        self._process(self.provider_code, response)

    def _send_capture_request(self):
        """ Override of `payment` to capture a pre-authorized amount. """
        if not self._is_hyperpay():
            return super()._send_capture_request()
        self._hyperpay_follow_up_request('CP', self.amount)

    def _send_void_request(self):
        """ Override of `payment` to reverse a pre-authorization. """
        if not self._is_hyperpay():
            return super()._send_void_request()
        self._hyperpay_follow_up_request('RV')

    def _send_refund_request(self):
        """ Override of `payment` to refund a captured amount. """
        if not self._is_hyperpay():
            return super()._send_refund_request()
        self._hyperpay_follow_up_request('RF', -self.amount)

    # === BUSINESS METHODS - PROCESSING === #

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """ Override of `payment` to extract the reference from the HyperPay data. """
        if provider_code not in self.env['payment.provider']._hyperpay_provider_codes():
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('merchantTransactionId')

    def _extract_amount_data(self, payment_data):
        """ Override of `payment` to extract the amount and currency from the HyperPay data. """
        if not self._is_hyperpay():
            return super()._extract_amount_data(payment_data)
        if payment_data.get('paymentType') == 'RV' or not payment_data.get('amount'):
            return None  # Reversals do not carry the amount: skip the validation.
        return {'amount': float(payment_data['amount']), 'currency_code': payment_data.get('currency')}

    def _apply_updates(self, payment_data):
        """ Override of `payment` to update the transaction based on the HyperPay data. """
        if not self._is_hyperpay():
            return super()._apply_updates(payment_data)

        result = payment_data.get('result') or {}
        result_code = result.get('code', '')
        description = result.get('description', '')
        payment_type = payment_data.get('paymentType')
        if payment_data.get('id'):
            self.provider_reference = payment_data['id']

        if any(re.match(pattern, result_code) for pattern in const.RESULT_CODES_SUCCESS):
            if payment_type == 'PA':
                self._set_authorized(state_message=description)
            elif payment_type == 'RV':
                self._set_canceled(state_message=description)
            else:  # DB, CP, RF
                self._set_done(state_message=description)
                if self.operation == 'refund':
                    self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif any(re.match(pattern, result_code) for pattern in const.RESULT_CODES_PENDING):
            self._set_pending(state_message=description)
        elif self.source_transaction_id:
            # A failed capture, void or refund must be visible to the accountant.
            self._set_error(_("HyperPay refused the operation: %(code)s %(desc)s",
                              code=result_code, desc=description))
        else:
            _logger.info("HyperPay declined transaction %s: %s %s", self.reference, result_code, description)
            self._set_canceled(state_message=description or result_code)
