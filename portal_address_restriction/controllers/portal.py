# -*- coding: utf-8 -*-
from werkzeug.exceptions import Forbidden

from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalAddressRestriction(CustomerPortal):
    """ Portal users cannot create, edit or remove addresses from their portal account. """

    @route()
    def portal_address(self, *args, **kwargs):
        if request.env.user._is_portal():
            return request.redirect('/my/addresses')
        return super().portal_address(*args, **kwargs)

    @route()
    def portal_address_submit(self, *args, **kwargs):
        if request.env.user._is_portal():
            raise Forbidden()
        return super().portal_address_submit(*args, **kwargs)
