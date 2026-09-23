import { patch } from '@web/core/utils/patch';
import { registry } from '@web/core/registry';
import { Interaction } from '@web/public/interaction';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    /**
     * @override
     * Send the sliced / shredded option and the number of pieces with the product
     * added to the cart (received as kwargs by `sale.order._cart_add`).
     */
    _updateRootProduct(form) {
        super._updateRootProduct(...arguments);
        const productEl = form.closest('.js_product') ?? form;
        const itemOption = productEl.querySelector('select[name="product_type_option"]')?.value;
        if (itemOption !== undefined) {
            this.rootProduct.productItemOption = itemOption;
            this.rootProduct.quantityPieces = parseInt(
                productEl.querySelector('input[name="quantity_pieces"]')?.value || 1
            );
        }
    },
});

export class ProductTypeOption extends Interaction {
    static selector = 'select[name="product_type_option"]';
    dynamicContent = {
        _root: { 't-on-change': this.onChange },
    };

    start() {
        this.onChange();
    }

    /**
     * Show the "No. of pieces" input only for sliced / shredded.
     */
    onChange() {
        const showPieces = Boolean(this.el.selectedOptions[0]?.dataset.showNoOfPieces);
        const wrapper = this.el.closest('.extra_fields')?.querySelector('#quantity_pieces_input_wrapper');
        wrapper?.classList.toggle('d-none', !showPieces);
    }
}

registry
    .category('public.interactions')
    .add('custom_saleorder_management.product_type_option', ProductTypeOption);
