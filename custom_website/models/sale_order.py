from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_salesperson_customer_id = fields.Many2one(
        'res.partner', string='Is SalesPerson Customer', copy=False,
        help="Customer a portal salesperson placed this web order for.")

    def action_confirm(self):
        res = super().action_confirm()
        for order in self.filtered(lambda o: o.website_id and o.is_salesperson_customer_id):
            if order.partner_id != order.is_salesperson_customer_id:
                order.partner_id = order.is_salesperson_customer_id
        return res

    def _is_reorder_allowed(self):
        self.ensure_one()
        return self.state in ['sale', 'jde_confirmed'] and any(
            line._is_reorder_allowed() for line in self.order_line if not line.display_type)

    def _update_address(self, partner_id, fnames=None):
        # The web shop resets the cart customer to the logged-in user on every request. Keep the
        # customer a salesperson is ordering for.
        user = self.env.user
        if (
            fnames == ['partner_id']
            and self.is_salesperson_customer_id
            and partner_id == user.partner_id.id
            and user.is_salesperson
            and self.is_salesperson_customer_id.user_id == user
        ):
            return
        return super()._update_address(partner_id, fnames)

    def _b2b_skip_online_payment(self):
        """ Orders confirmed without online payment: orders placed by a salesperson, and
        customers on credit (any payment term other than cash-to-deliver 'CTD'). """
        self.ensure_one()
        if self.is_salesperson_customer_id:
            return True
        term = self.partner_id.commercial_partner_id.property_payment_term_id or self.partner_id.property_payment_term_id
        return not term or (bool(term.b2b_code) and term.b2b_code != 'CTD')

    def get_jde_order_status(self):
        """ True when JDE has printed the invoice of every delivery that was not cancelled. """
        self.ensure_one()
        invoice_printed = self.picking_ids.filtered(lambda p: p.jde_state == 'invoice_printed')
        if not invoice_printed:
            return False
        others = self.picking_ids - invoice_printed
        return all(p.jde_state == 'cancel' for p in others)
