# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2023. All rights reserved.
# Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('applepay', 'Apple Pay')], ondelete={'applepay': 'set default'})
    applepay_entity_id = fields.Char(
        string='Merchant ID/Entity Id', required_if_provider='applepay', groups='base.group_system',
        help="The HyperPay entity id configured for Apple Pay.")
    applepay_authorization_bearer = fields.Char(
        string='Authorization Bearer', required_if_provider='applepay', groups='base.group_system',
        help="The HyperPay access token (sent as 'Authorization: Bearer <token>').")
    applepay_display_name = fields.Char(
        string="Apple Pay Display Name", help="Merchant name shown on the Apple Pay payment sheet.")
    applepay_merchant_identifier = fields.Char(
        string="Apple Merchant Identifier",
        help="Apple Pay merchant identifier (e.g. merchant.com.example). When set, the Apple Pay button "
             "is only shown on devices with an active card for this merchant.")
    applepay_supported_networks = fields.Char(
        string="Supported Networks", default="masterCard,visa",
        help="Comma-separated Apple Pay networks, e.g. masterCard,visa,mada.")
    applepay_supported_countries = fields.Char(
        string="Supported Countries", default="AE",
        help="Comma-separated ISO country codes of the cards accepted, e.g. AE,SA.")

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        self.ensure_one()
        if self.code != 'applepay':
            return super()._get_default_payment_method_codes()
        return {'Applepay'}

    # === BUSINESS METHODS - HYPERPAY === #

    def _hyperpay_provider_codes(self):
        return super()._hyperpay_provider_codes() | {'applepay'}

    def _hyperpay_get_access_token(self):
        if self.code != 'applepay':
            return super()._hyperpay_get_access_token()
        return self.sudo().applepay_authorization_bearer

    def _hyperpay_get_entity_id(self, payment_method):
        if self.code != 'applepay':
            return super()._hyperpay_get_entity_id(payment_method)
        return self.sudo().applepay_entity_id

    def _hyperpay_get_brands(self, payment_method):
        if self.code != 'applepay':
            return super()._hyperpay_get_brands(payment_method)
        return 'APPLEPAY'

    def _hyperpay_get_widget_options(self, tx):
        if self.code != 'applepay':
            return super()._hyperpay_get_widget_options(tx)
        display_name = self.applepay_display_name or tx.company_id.name
        apple_pay = {
            'displayName': display_name,
            'total': {'label': display_name},
            'supportedNetworks': [n.strip() for n in (self.applepay_supported_networks or '').split(',') if n.strip()],
            'supportedCountries': [c.strip() for c in (self.applepay_supported_countries or '').split(',') if c.strip()],
            'currencyCode': tx.currency_id.name,
            'buttonType': 'buy',
            'buttonStyle': 'black',
        }
        if self.applepay_merchant_identifier:
            apple_pay.update({
                'version': 3,
                'checkAvailability': 'applePayCapabilities',
                'merchantIdentifier': self.applepay_merchant_identifier,
            })
        return {'applePay': apple_pay}
