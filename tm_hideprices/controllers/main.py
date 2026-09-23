from odoo import _
from odoo.exceptions import AccessError
from odoo.http import request, route

from odoo.addons.website_sale.controllers.cart import Cart


class CartHidePrices(Cart):
    """ Visitors who are not logged in cannot buy: they must log in first.
    (`/shop/cart/quick_add` already requires a logged-in user in 19.0.) """

    def _b2b_check_logged_in(self):
        if request.env.user._is_public():
            raise AccessError(_("Please log in to add products to your cart."))

    @route()
    def add_to_cart(self, *args, **kwargs):
        self._b2b_check_logged_in()
        return super().add_to_cart(*args, **kwargs)

    @route()
    def update_cart(self, *args, **kwargs):
        self._b2b_check_logged_in()
        return super().update_cart(*args, **kwargs)
