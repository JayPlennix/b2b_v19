import logging
from datetime import datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PricelistAPI(http.Controller):

    @http.route('/api/product-pricelist', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_pricelist_api(self, **post):
        try:
            datas = post.get('data')

            product_pricelist_dict = {}
            price_lst = []
            for data in datas:
                product_pricelist = self.create_pricelist(data)
                if isinstance(product_pricelist, dict):
                    product_pricelist_dict = product_pricelist
                    break

                if product_pricelist and product_pricelist.id not in price_lst:
                    price_lst.append(product_pricelist.id)

            if product_pricelist_dict:
                return product_pricelist_dict

            if price_lst:
                return self.create_response(True,
                                            {'product_pricelist': price_lst},
                                            'Product pricelist Updated', 200)
            else:
                return self.create_response(False,
                                            {'product_pricelist': price_lst},
                                            'Product pricelist data Error', 400)

        except Exception as e:
            return {'error': str(e)}

    def find_product_by_jde_code(self, jde_product_id):
        return request.env['product.template'].search([("jde_product_id", '=', jde_product_id)], limit=1)

    def find_product_pricelist_name(self, pricelist_name):
        return request.env['product.pricelist'].search([("name", '=', pricelist_name)], limit=1)

    def find_related_customer(self, customer_id):
        return request.env['res.partner'].search([("b2b_customer_id", '=', customer_id)], limit=1)

    def parse_date(self, date_string):
        try:
            if date_string:
                date_format = "%m/%d/%Y %H:%M:%S"
                return datetime.strptime(date_string, date_format)
            else:
                return False
        except ValueError as ve:
            _logger.error('ValueError in parse_date: %s', ve)
            raise ve

    def create_pricelist(self, data):
        try:
            # Roll back partial writes: errors are returned to JDE, not raised,
            # so the request transaction would otherwise be committed.
            with request.env.cr.savepoint():
                currency = request.env['res.currency'].search([("name", '=', data.get('currency_id'))], limit=1)

                company = False
                if 'source' in data and data.get('source'):
                    company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)
                company_id = company.id if company else data.get('company_id')

                website = request.env['website'].sudo().search([('company_id', '=', company_id)], limit=1)

                pricelist_vals = {
                    'name': data.get('name'),
                    'company_id': company_id,
                    'website_id': website.id if website else False,
                    'currency_id': currency.id if currency else False,
                    'active': True
                }
                exist_pricelist = self.find_product_pricelist_name(data.get('name'))
                related_customer = self.find_related_customer(data.get("customer_id"))
                if not related_customer:
                    return self.create_response(False,
                                                {},
                                                'Related Customer Not Existing', 200)
                if exist_pricelist:
                    product_pricelist = exist_pricelist
                else:
                    product_pricelist = request.env['product.pricelist'].create(pricelist_vals)

                product_pricelist_vals = self.prepare_pricelist_items_vals(data, product_pricelist)
                if isinstance(product_pricelist_vals, dict):
                    return product_pricelist_vals
                request.env['product.pricelist.item'].create(product_pricelist_vals)

                company = request.env['res.company'].sudo().browse(company_id).exists()
                related_customer.with_company(company).write({'property_product_pricelist': product_pricelist.id})

                for child in related_customer.child_ids:
                    child.sudo().with_company(company).write({'property_product_pricelist': product_pricelist.id})

                return product_pricelist

        except Exception as e:
            return {'error': str(e)}

    def prepare_pricelist_items_vals(self, data, product_pricelist):
        product_pricelist_rule_data = data.get('product_pricelist_rules')
        vals = []
        for product_rule in product_pricelist_rule_data:
            product_id_data = product_rule['product_id']
            product_items_exist = self.find_product_by_jde_code(product_id_data)
            if not product_items_exist:
                return self.create_response(False,
                                            {'product_id': product_id_data},
                                            'Product_id Not Existing Product', 200)

            start_date_obj = datetime.strptime(product_rule.get('date_start'), "%m/%d/%Y")
            end_date_obj = datetime.strptime(product_rule.get('date_end'), "%m/%d/%Y")

            product_pricelist_item = request.env['product.pricelist.item'].search([
                ('pricelist_id', '=', product_pricelist.id),
                ('product_tmpl_id', '=', product_items_exist.id),
                ('date_start', '=', start_date_obj),
                ('date_end', '=', end_date_obj),
                ('company_id', '=', product_pricelist.company_id.id),
            ])
            if product_pricelist_item:
                product_pricelist_item.sudo().write({
                    'fixed_price': product_rule.get('fixed_price'),
                })
            else:
                vals.append({
                    'pricelist_id': product_pricelist.id,
                    'product_tmpl_id': product_items_exist.id,
                    'company_id': product_pricelist.company_id.id,
                    'fixed_price': product_rule.get('fixed_price'),
                    'date_start': start_date_obj,
                    'date_end': end_date_obj,
                })
        return vals

    def create_response(self, success, response, message, status):
        return {'success': success, 'response': response, 'message': message, 'status': status}
