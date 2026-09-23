from odoo import fields, models
from odoo.fields import Domain
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    is_ksa = fields.Boolean(string='Is Transmed KSA')
    is_jordan = fields.Boolean(string='Is Transmed Jordan')

    def _get_product_available_qty(self, product, **kwargs):
        # B2B customers see the stock of their own warehouse location.
        location = not self.env.user._is_public() and self.env.user.partner_id.customer_location_id
        if location:
            return product.with_context(warehouse_id=self.warehouse_id.id, location=location.id).free_qty
        return super()._get_product_available_qty(product, **kwargs)

    def _prepare_sale_order_values(self, partner_sudo):
        # Contacts of a company always invoice the company.
        values = super()._prepare_sale_order_values(partner_sudo)
        if partner_sudo.parent_id:
            values['partner_invoice_id'] = partner_sudo.parent_id.address_get(['invoice'])['invoice']
        return values

    def sale_product_domain(self):
        domain = Domain(super().sale_product_domain())
        user = self.env.user
        if user._is_internal():
            return domain
        partner = user.partner_id
        # Products limited to specific customers.
        domain &= Domain('limited_item_ids', '=', False) | Domain('limited_item_ids', 'in', partner.ids)
        # KSA: only the products stocked in the customer's location (when that location has stock).
        website = self or self.get_current_website()
        location = not user._is_public() and partner.customer_location_id
        if website.company_id.is_ksa and location:
            quants = self.env['stock.quant'].sudo().search([('location_id', '=', location.id)])
            if quants:
                domain &= Domain('id', 'in', quants.product_id.product_tmpl_id.ids)
        return domain

    def _get_checkout_step_values(self):
        # Always show the checkout (address) page: salespersons choose the customer there.
        values = super()._get_checkout_step_values()
        if values.get('next_website_checkout_step_href') == '/shop/checkout?try_skip_step=true':
            values['next_website_checkout_step_href'] = '/shop/checkout'
        return values
