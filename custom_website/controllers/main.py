import logging

from werkzeug.exceptions import Forbidden, NotFound

from odoo.http import request, route

from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist

_logger = logging.getLogger(__name__)

PORTAL_ORDER_STATES = [
    'sale', 'jde_confirmed', 'credit_control', 'order_at_WH', 'order_confirmed', 'ready_to_ship', 'invoice_printed',
]


class CustomerPortalB2B(sale_portal.CustomerPortal):
    # Each contact sees their own orders (not the whole company's) and the orders they follow
    # (a salesperson follows the orders placed for their customers), including orders confirmed
    # in JD Edwards.

    def _b2b_portal_partner_domain(self, partner):
        return ['|', ('partner_id', 'child_of', [partner.id]), ('message_partner_ids', 'child_of', [partner.id])]

    def _prepare_quotations_domain(self, partner):
        return [*self._b2b_portal_partner_domain(partner), ('state', '=', 'sent')]

    def _prepare_orders_domain(self, partner):
        return [*self._b2b_portal_partner_domain(partner), ('state', 'in', PORTAL_ORDER_STATES)]


class WebsiteSaleB2B(WebsiteSale):

    # === Shop: brand filter (/shop?brand_id=<id>) === #

    def _get_search_options(self, *args, **post):
        options = super()._get_search_options(*args, **post)
        if post.get('brand_id'):
            options['brand_id'] = post['brand_id']
        return options

    @route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        # Products reserved to other customers (or not stocked in their KSA location) cannot be
        # opened by URL either.
        if not product.sudo().filtered_domain(request.website.sale_product_domain()):
            raise NotFound()
        return super().product(product, category=category, pricelist=pricelist, **kwargs)

    def _shop_get_query_url_kwargs(self, *args, **kwargs):
        query_kwargs = super()._shop_get_query_url_kwargs(*args, **kwargs)
        if kwargs.get('brand_id'):
            query_kwargs['brand_id'] = kwargs['brand_id']
        return query_kwargs

    # === Checkout: salesperson ordering for a customer === #

    @route('/shop/salesperson/customer', type='http', methods=['POST'], auth='user', website=True, sitemap=False)
    def shop_salesperson_customer(self, customer_id=None, **kwargs):
        """ Let a portal salesperson place the cart for one of their customers (or themselves). """
        user = request.env.user
        order_sudo = request.cart
        if not user.is_salesperson or not order_sudo:
            raise Forbidden()
        customer_id = int(customer_id or 0)
        if customer_id:
            customer = user._get_b2b_customers().filtered(lambda p: p.id == customer_id)
            if not customer:
                raise Forbidden()
            order_sudo.is_salesperson_customer_id = customer
            order_sudo._update_address(customer.id, ['partner_id'])
            order_sudo._update_address(customer.address_get(['invoice'])['invoice'], ['partner_invoice_id'])
            order_sudo.message_subscribe(partner_ids=user.partner_id.ids)
        else:
            order_sudo.is_salesperson_customer_id = False
            order_sudo._update_address(user.partner_id.id, ['partner_id'])
        return request.redirect('/shop/checkout')

    def _prepare_checkout_page_values(self, order_sudo, **kwargs):
        values = super()._prepare_checkout_page_values(order_sudo, **kwargs)
        user = request.env.user
        if user.is_salesperson:
            values.update({
                'b2b_salesperson_customers': user._get_b2b_customers(),
                'b2b_selected_customer': order_sudo.is_salesperson_customer_id,
            })
        return values

    def _prepare_address_data(self, partner_sudo, **kwargs):
        # Contacts of a company always invoice the company.
        values = super()._prepare_address_data(partner_sudo, **kwargs)
        if partner_sudo.parent_id:
            values['billing_addresses'] = partner_sudo.parent_id.with_context(show_address=1)
        return values

    # === Checkout: addresses are maintained by Transmed (customers contact support) === #

    def _b2b_can_edit_addresses(self):
        user = request.env.user
        return user._is_public() or user._is_internal() or user.is_salesperson

    @route()
    def shop_address(self, *args, **kwargs):
        if not self._b2b_can_edit_addresses():
            return request.redirect('/contactus')
        return super().shop_address(*args, **kwargs)

    @route()
    def shop_address_submit(self, *args, **kwargs):
        if not self._b2b_can_edit_addresses():
            raise Forbidden()
        return super().shop_address_submit(*args, **kwargs)

    # === Checkout: customers on credit and salesperson orders skip online payment === #

    @route()
    def shop_payment(self, **post):
        order_sudo = request.cart
        if order_sudo and order_sudo._b2b_skip_online_payment():
            # As in 17.0, no Odoo delivery method is required: delivery charges come from JDE.
            if redirection := self._check_cart_and_addresses(order_sudo):
                return redirection
            # Delivery charges come from JDE: no carrier, no delivery line.
            order_sudo.carrier_id = False
            order_sudo._remove_delivery_line()
            request.session['sale_last_order_id'] = order_sudo.id
            order_sudo.with_context(send_email=True).action_confirm()
            request.website.sale_reset()
            return request.redirect('/shop/confirmation')
        return super().shop_payment(**post)

    # === Wishlist: logged-in customers only === #

    def _get_additional_shop_values(self, values, **kwargs):
        vals = super()._get_additional_shop_values(values, **kwargs)
        if request.env.user._is_public():
            vals['products_in_wishlist'] = None  # Hides the wishlist button on product tiles.
        return vals


class WishlistB2B(WebsiteSaleWishlist):

    @route()
    def get_wishlist(self, **kw):
        if request.env.user._is_public():
            return request.redirect('/web/login?redirect=/shop/wishlist')
        return super().get_wishlist(**kw)

    @route()
    def add_to_wishlist(self, product_id, **kw):
        if request.env.user._is_public():
            return False
        return super().add_to_wishlist(product_id, **kw)
