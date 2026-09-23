# -*- coding: utf-8 -*-
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _can_be_edited_by_current_customer(self, **kwargs):
        # Addresses are maintained by Transmed: portal users (customers and salespersons)
        # cannot edit or remove any address, on My Account, My Addresses or the checkout.
        if self.env.user._is_portal():
            return False
        return super()._can_be_edited_by_current_customer(**kwargs)
