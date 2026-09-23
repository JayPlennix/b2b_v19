from datetime import datetime, timedelta

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):

    @route()
    def shop_checkout(self, try_skip_step=None, **query_params):
        res = super().shop_checkout(try_skip_step=try_skip_step, **query_params)
        # Orders placed before 16:00 are expected the next day, later orders the day after.
        if order_sudo := request.cart:
            current_time = datetime.now()
            if current_time.hour < 16:
                order_sudo.commitment_date = current_time + timedelta(days=1)
            else:
                order_sudo.commitment_date = current_time + timedelta(days=2)
        return res
