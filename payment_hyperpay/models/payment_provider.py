# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
#
#################################################################################
import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_hyperpay import const

_logger = get_payment_logger(__name__, sensitive_keys={'Authorization'})

REQUEST_TIMEOUT = 60


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('hyperpay', 'HyperPay')], ondelete={'hyperpay': 'set default'})
    hyperpay_merchant_id = fields.Char(
        string="Entity Id", required_if_provider='hyperpay', groups='base.group_system',
        help="The HyperPay entity id used for card payments.")
    hyperpay_mada_entity_id = fields.Char(
        string="Mada Entity Id", groups='base.group_system',
        help="HyperPay usually issues a separate entity id for mada cards. Leave empty to use the main one.")
    hyperpay_authorization = fields.Char(
        string="Access Token", required_if_provider='hyperpay', groups='base.group_system',
        help="The HyperPay access token (sent as 'Authorization: Bearer <token>').")

    # === COMPUTE METHODS === #

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code in self._hyperpay_provider_codes()).update({
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
        })

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        self.ensure_one()
        if self.code != 'hyperpay':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === BUSINESS METHODS - HYPERPAY === #

    def _hyperpay_provider_codes(self):
        """ Provider codes processed through HyperPay COPYandPAY (extended by payment_applepay). """
        return {'hyperpay'}

    def _hyperpay_get_domain(self):
        """ HyperPay API host. Can be overridden with the system parameters
        `payment_hyperpay.live_domain` / `payment_hyperpay.test_domain` (e.g. https://oppwa.com). """
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        if self.state == 'enabled':
            return params.get_param('payment_hyperpay.live_domain') or const.LIVE_DOMAIN
        return params.get_param('payment_hyperpay.test_domain') or const.TEST_DOMAIN

    def _hyperpay_get_access_token(self):
        self.ensure_one()
        return self.sudo().hyperpay_authorization

    def _hyperpay_get_entity_id(self, payment_method):
        """ Return the entity id to use for a payment with the given payment method. """
        self.ensure_one()
        provider = self.sudo()
        if payment_method.code == 'mada' and provider.hyperpay_mada_entity_id:
            return provider.hyperpay_mada_entity_id
        return provider.hyperpay_merchant_id

    def _hyperpay_get_brands(self, payment_method):
        """ Return the COPYandPAY `data-brands` for the given payment method. """
        self.ensure_one()
        if payment_method.code in const.PAYMENT_METHODS_MAPPING:
            return const.PAYMENT_METHODS_MAPPING[payment_method.code]
        # Generic card: offer the card brands activated on the provider.
        brands = [
            const.PAYMENT_METHODS_MAPPING[pm.code]
            for pm in self.payment_method_ids.brand_ids.filtered('active') | self.payment_method_ids
            if pm.code in const.PAYMENT_METHODS_MAPPING and pm.code != 'mada'
        ]
        return ' '.join(dict.fromkeys(brands)) or const.DEFAULT_BRANDS

    def _hyperpay_get_widget_options(self, tx):
        """ Return the `wpwlOptions` of the COPYandPAY widget (overridden by payment_applepay). """
        return {'style': 'card', 'locale': (tx.partner_lang or 'en')[:2]}

    def _hyperpay_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request to the HyperPay API, log it in the integration log and return the JSON
        response.

        :raise ValidationError: If the API cannot be reached or does not return JSON.
        """
        self.ensure_one()
        url = self._hyperpay_get_domain() + endpoint
        headers = {'Authorization': 'Bearer ' + (self._hyperpay_get_access_token() or '')}
        log = self.env['integration.log'].sudo().create({
            'name': f"HyperPay {method} {endpoint.split('?')[0]}",
            'url': url,
            'headers': str({'Authorization': 'Bearer ***'}),
            'payload': str(data or {}),
        })
        try:
            if method == 'GET':
                response = requests.get(url, params=data, headers=headers, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(url, data=data, headers=headers, timeout=REQUEST_TIMEOUT)
            log.response = response.text
            response_content = response.json()
        except (requests.exceptions.RequestException, ValueError) as error:
            log.response = str(error)
            _logger.exception("Unable to reach HyperPay at %s", url)
            raise ValidationError(_("HyperPay: Could not establish the connection to the API.")) from error
        return response_content
