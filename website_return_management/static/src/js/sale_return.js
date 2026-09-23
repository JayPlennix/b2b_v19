/**
 * Cybrosys Technologies Pvt. Ltd. — AGPL-3
 * Odoo 19.0 migration: Plennix Technologies
 */
import { _t } from '@web/core/l10n/translation';
import { registry } from '@web/core/registry';
import { Interaction } from '@web/public/interaction';
import { ConfirmationDialog } from '@web/core/confirmation_dialog/confirmation_dialog';

export class SaleReturnForm extends Interaction {
    static selector = '#quote_content';
    dynamicContent = {
        '#hidden_box_btn': { 't-on-click.prevent': this.onOpenDialog },
        '#product': { 't-on-change': this.onProductChange },
        '#qty': { 't-on-change': this.onQuantityChange },
        '#o_website_form_result': { 't-on-submit': this.onSubmit },
    };

    get quantityInput() {
        return this.el.querySelector('#qty');
    }

    get selectedOption() {
        return this.el.querySelector('#product')?.selectedOptions[0];
    }

    get deliveredQuantity() {
        return parseFloat(this.selectedOption?.dataset.qty_delivered) || 0;
    }

    warn(message) {
        this.services.dialog.add(ConfirmationDialog, { title: _t("Validation"), body: message });
    }

    onOpenDialog() {
        window.Modal.getOrCreateInstance(this.el.querySelector('#hidden_box')).show();
    }

    onProductChange(ev) {
        // The submit button only shows once a product is selected.
        this.el.querySelector('#submit')?.classList.toggle('d-none', ev.currentTarget.value === 'none');
    }

    onQuantityChange(ev) {
        const delivered = this.deliveredQuantity;
        if (parseFloat(ev.currentTarget.value) > delivered) {
            ev.currentTarget.value = delivered;
            this.warn(_t("You can't return more than the delivered quantity."));
        }
    }

    onSubmit(ev) {
        if (!(parseFloat(this.quantityInput?.value) >= 1)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.warn(_t("You can't submit without a return quantity."));
        }
    }
}

registry.category('public.interactions').add('website_return_management.sale_return_form', SaleReturnForm);
