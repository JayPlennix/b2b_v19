import { _t } from '@web/core/l10n/translation';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { rpc } from '@web/core/network/rpc';
import { registry } from '@web/core/registry';
import { Interaction } from '@web/public/interaction';

export class SaleTrackingOrder extends Interaction {
    static selector = '#tracking_sale_order';
    dynamicContent = {
        _root: { 't-on-click.prevent': this.onTrackingSaleOrder },
    };

    async onTrackingSaleOrder() {
        const saleOrderId = parseInt(this.el.dataset.saleOrderId);
        if (!saleOrderId) {
            return;
        }
        const result = await this.waitFor(rpc('/tracking_sale_order', {
            sale_order_id: saleOrderId,
            access_token: new URLSearchParams(window.location.search).get('access_token'),
        }));
        if (result && result.redirect) {
            this.showTrackingInfo(result.driver, result.vehicle);
            window.open(result.url, '_blank');
        } else {
            // JDE only sends the driver position once the delivery has left the warehouse.
            this.services.dialog.add(AlertDialog, {
                title: _t("Track Order"),
                body: _t("Live tracking is available once your delivery is on its way."),
            });
        }
    }

    showTrackingInfo(driver, vehicle) {
        document.getElementById('customTrackingSaleOrderInfo')?.remove();
        const infoDiv = document.createElement('div');
        infoDiv.id = 'customTrackingSaleOrderInfo';
        Object.assign(infoDiv.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: 'rgb(236, 236, 236)',
            padding: '20px',
            zIndex: '1000',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
            border: '1px solid #ddd',
            borderRadius: '5px',
        });
        const title = document.createElement('h4');
        title.textContent = _t('Tracking Information');
        const driverEl = document.createElement('p');
        driverEl.textContent = `${_t('Driver : ')} ${driver || ''}`;
        const vehicleEl = document.createElement('p');
        vehicleEl.textContent = `${_t('Vehicle : ')} ${vehicle || ''}`;
        const closeButton = document.createElement('button');
        closeButton.className = 'btn btn-primary btn-sm';
        closeButton.textContent = _t('Close');
        infoDiv.append(title, driverEl, vehicleEl, closeButton);
        infoDiv.addEventListener('click', () => infoDiv.remove());
        document.body.appendChild(infoDiv);
        setTimeout(() => infoDiv.remove(), 60000);
    }
}

registry
    .category('public.interactions')
    .add('custom_saleorder_management.sale_tracking_order', SaleTrackingOrder);
