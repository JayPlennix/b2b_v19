from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    high_review_product = fields.Boolean(string='Is High Review')
    best_selling_product = fields.Boolean(string='Is Best Selling')


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    is_featured_category = fields.Boolean(string='Is Featured Category')
    is_main_category = fields.Boolean(string='Is Main Category')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    limited_item_ids = fields.Many2many(
        'res.partner', string="Limited Items",
        help="When set, the product is only visible on the web shop for these customers.")
    is_ksa = fields.Boolean(string='Is Transmed KSA', related="company_id.is_ksa", store=True)
    is_jordan = fields.Boolean(string='Is Transmed Jordan', related="company_id.is_jordan", store=True)

    # === Prices per kg for products sold by the gram === #

    def _b2b_price_display(self):
        """ Return (factor, unit label) used to display the web shop price.

        Products sold by the gram are displayed per kg (price x 1000); others per their unit.
        """
        self.ensure_one()
        gram = self.env.ref('uom.product_uom_gram', raise_if_not_found=False)
        if gram and self.uom_id == gram:
            return 1000, 'KG'
        return 1, self.uom_id.name or ''

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        info = super()._get_additionnal_combination_info(product_or_template, quantity, uom, date, website)
        if self.env.context.get('b2b_search_result'):
            factor = product_or_template.product_tmpl_id._b2b_price_display()[0] \
                if product_or_template._name == 'product.product' else product_or_template._b2b_price_display()[0]
            if factor != 1:
                info['price'] = info['price'] * factor
        return info

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        return super(ProductTemplate, self.with_context(b2b_search_result=True))._search_render_results(
            fetch_fields, mapping, icon, limit)

    @api.model
    def _apply_taxes_to_price(self, price, currency, product_taxes, taxes, product_or_template, website=None):
        # Unit prices of products sold by the gram are tiny: do not round the per-unit tax,
        # otherwise the per-kg price shown (x 1000) drifts.
        return super()._apply_taxes_to_price(
            price, currency, product_taxes, taxes.with_context(round=False, round_base=False),
            product_or_template, website=website)

    # === Shop brand filter (/shop?brand_id=<id>) === #

    @api.model
    def _search_get_detail(self, website, order, options):
        detail = super()._search_get_detail(website, order, options)
        brand_id = options.get('brand_id')
        if brand_id and str(brand_id).isdigit():
            detail['base_domain'] = [*detail['base_domain'], [('brand_id', '=', int(brand_id))]]
        return detail
