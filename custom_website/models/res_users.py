from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_salesperson = fields.Boolean(
        string='Is SalesPerson',
        help="Portal salesperson: can place web shop orders on behalf of the customers assigned to "
             "them (customers whose Salesperson is this user).")

    def _get_b2b_customers(self):
        """ Customers this salesperson may order for. """
        self.ensure_one()
        if not self.is_salesperson:
            return self.env['res.partner']
        return self.env['res.partner'].sudo().search([('user_id', '=', self.id)], order='name')
