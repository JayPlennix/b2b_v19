# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
#
#################################################################################
import json
import pprint
from urllib.parse import urlencode

from markupsafe import Markup

from werkzeug.exceptions import Forbidden


from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import urls

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger

_logger = get_payment_logger(__name__)


class HyperPayController(http.Controller):
    _checkout_url = '/payment/hyperpay/checkout'
    _return_url = '/payment/hyperpay/return'

    @http.route(_checkout_url, type='http', auth='public', methods=['POST'], csrf=False, website=True)
    def hyperpay_checkout(self, reference=None, access_token=None, **kwargs):
        """ Show the HyperPay COPYandPAY payment widget for the transaction.

        Reached through the redirect form of the transaction (see `_get_specific_rendering_values`).
        """
        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
        if not tx_sudo or not tx_sudo._is_hyperpay() or not payment_utils.check_access_token(
                access_token, tx_sudo.reference, tx_sudo.amount):
            raise Forbidden()
        if tx_sudo.state != 'draft':
            return request.redirect('/payment/status')

        try:
            checkout_id = tx_sudo._hyperpay_create_checkout()
        except ValidationError as error:
            tx_sudo._set_error(str(error))
            checkout_id = False
        if not checkout_id:
            return request.redirect('/payment/status')

        provider_sudo = tx_sudo.provider_id
        base_url = provider_sudo.get_base_url()
        return request.render('payment_hyperpay.checkout_page', {
            'tx': tx_sudo,
            'widget_url': f'{provider_sudo._hyperpay_get_domain()}/v1/paymentWidgets.js?checkoutId={checkout_id}',
            'result_url': urls.urljoin(base_url, f'{self._return_url}?{urlencode({"reference": tx_sudo.reference})}'),
            'brands': provider_sudo._hyperpay_get_brands(tx_sudo.payment_method_id),
            # Inlined in a <script>: escape '<' so the JSON can never close the tag.
            'wpwl_script': Markup('var wpwlOptions = %s;' % json.dumps(
                provider_sudo._hyperpay_get_widget_options(tx_sudo)).replace('<', '\\u003c')),
        })

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def hyperpay_return(self, reference=None, id=None, resourcePath=None, **kwargs):
        """ Process the payment result after the customer submitted the COPYandPAY widget.

        The result is always fetched from HyperPay with our credentials; the reference of the
        fetched payment must match the transaction.
        """
        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
        if (tx_sudo and tx_sudo._is_hyperpay() and id and id == tx_sudo.hyperpay_checkout_id
                and resourcePath and resourcePath.startswith(f'/v1/checkouts/{id}/')):
            try:
                payment_data = tx_sudo._hyperpay_fetch_payment_result(resourcePath)
            except ValidationError as error:
                tx_sudo._set_error(str(error))
            else:
                _logger.info("HyperPay payment result for %s:\n%s", tx_sudo.reference, pprint.pformat(payment_data))
                if payment_data.get('merchantTransactionId') == tx_sudo.reference:
                    tx_sudo._process(tx_sudo.provider_code, payment_data)
                else:
                    _logger.warning("HyperPay result does not belong to transaction %s", tx_sudo.reference)
        else:
            _logger.warning("Invalid HyperPay return for reference %s", reference)
        return request.redirect('/payment/status')
