/**
 * "Order Again" fails silently in 19.0 (the error only reaches the browser console), which
 * looks like a dead button. Show the reason to the customer instead.
 */
import { browser } from '@web/core/browser/browser';
import { _t } from '@web/core/l10n/translation';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { rpc } from '@web/core/network/rpc';
import { redirect } from '@web/core/utils/urls';
import { patch } from '@web/core/utils/patch';

import { SaleOrderPortalReorder } from '@website_sale/interactions/reorder';

patch(SaleOrderPortalReorder.prototype, {
    async _doReorder() {
        try {
            const values = await this.waitFor(rpc('/my/orders/reorder', {
                order_id: this.orderId,
                access_token: this.accessToken,
            }));
            browser.sessionStorage.setItem('website_sale_cart_quantity', values.cart_quantity);
            this._trackProducts(values.tracking_info);
            redirect('/shop/cart');
        } catch (error) {
            this.services.dialog.add(AlertDialog, {
                title: _t("Order Again"),
                body: error?.data?.message || error?.message
                    || _t("This order could not be added to your cart."),
            });
        }
    },
});
