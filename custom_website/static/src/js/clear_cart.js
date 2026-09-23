import { rpc } from '@web/core/network/rpc';
import { registry } from '@web/core/registry';
import { Interaction } from '@web/public/interaction';

export class B2BClearCart extends Interaction {
    static selector = '.js_b2b_clear_cart';
    dynamicContent = {
        _root: { 't-on-click.prevent': this.locked(this.onClick, true) },
    };

    async onClick() {
        await this.waitFor(rpc('/shop/cart/clear'));
        window.location = '/shop/cart';
    }
}

registry.category('public.interactions').add('custom_website.clear_cart', B2BClearCart);
