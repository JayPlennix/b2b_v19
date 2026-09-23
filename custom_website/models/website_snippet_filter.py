from odoo import _, api, models
from odoo.exceptions import ValidationError


class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    @api.constrains('limit')
    def _check_limit(self):
        """ Transmed shows up to 50 featured categories / products (core: 16). """
        for record in self:
            if not 0 < record.limit <= 50:
                raise ValidationError(_("The limit must be between 1 and 50."))
