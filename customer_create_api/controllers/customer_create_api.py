import logging
from datetime import datetime

from odoo import Command, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PartnerAPI(http.Controller):

    @http.route('/api/partners', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_customer_api(self, **post):
        try:
            data = post
            customer_exist = self.find_customer_by_b2b_id(data.get('b2b_customer_id'))

            if customer_exist:
                message = 'Already Existing Customer_id'
                if not customer_exist.active:
                    message = 'Already Existing Customer_id but is Archived'
                return self.create_response(False,
                                            {'customer_name': customer_exist.name, 'customer_id': customer_exist.id},
                                            message, 200)

            partner = self.create_partner(data)
            if isinstance(partner, dict):
                return str(partner)

            elif hasattr(partner, 'id'):
                return self.create_response(True,
                                            {'customer_id': partner.id, 'customer_name': partner.name},
                                            'Customer Created', 200)
            else:
                return self.create_response(False,
                                            {"partner": partner},
                                            'Customer data Error', 400)
        except Exception as e:
            return {'error': str(e)}

    def find_customer_by_b2b_id(self, b2b_customer_id):
        return request.env['res.partner'].with_context(active_test=False).search(
            [("b2b_customer_id", '=', b2b_customer_id)], limit=1)

    def create_partner(self, data):
        try:
            # Roll back partial writes: errors are returned to JDE, not raised,
            # so the request transaction would otherwise be committed.
            with request.env.cr.savepoint():
                country_id = self.get_country_id(data)
                state_id = self.get_state_id(data)
                datejde_object = self.parse_date(data.get('timestamp_jde'))

                parent_data = data.get('parent_id')
                if parent_data == data.get('b2b_customer_id'):
                    delivery_address = self.create_delivery_address(data, state_id, country_id)
                else:
                    delivery_address = None
                parent_id = self.get_parent_id(data)
                sale_person_id = self.get_saleperson_id(data)
                vals = self.prepare_partner_vals(data, country_id, state_id, datejde_object, parent_id, delivery_address,
                                                 sale_person_id)
                partner = request.env['res.partner'].with_context(_partners_skip_fields_sync=True).create(vals)
                partner.with_company(partner.company_id).property_payment_term_id = self.get_payment_term_b2b(data)
                return partner

        except Exception as e:
            return {'error': str(e)}

    def get_country_id(self, data):
        try:
            country = data.get('country')
            if not country:
                return {"country_id": False}

            country_id = request.env['res.country'].search(
                ['|', ("name", 'ilike', country), ("code", 'ilike', country)], limit=1)
            return {"country_id": country_id.id if country_id else False}

        except ValueError as ve:
            _logger.error('ValueError in get_country_id: %s', ve)
            return {'error': f'ValueError: {ve}'}

        except Exception as e:
            _logger.error('Error in get_country_id: %s', e)
            return {'error': str(e)}

    def get_state_id(self, data):
        try:
            state = data.get('state')
            if not state:
                return {"state_id": False}

            state_id = request.env['res.country.state'].search(
                ['|', ("name", 'ilike', state), ("code", 'ilike', state)], limit=1)
            return {"state_id": state_id.id if state_id else False}

        except ValueError as ve:
            _logger.error('ValueError in get_state_id: %s', ve)
            return {'error': f'ValueError: {ve}'}

        except Exception as e:
            _logger.error('Error in get_state_id: %s', e)
            return {'error': str(e)}

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

    def get_parent_id(self, data):
        parent_id = data.get('parent_id')
        if parent_id:
            parent_exist_id = self.find_customer_by_b2b_id(parent_id)
            if parent_exist_id:
                return parent_exist_id.id
        return False

    def get_saleperson_id(self, data):
        saleperson_id = data.get('saleperson_id')
        if saleperson_id and saleperson_id != 'null':
            saleperson_exist_id = self.find_customer_by_b2b_id(saleperson_id)
            if saleperson_exist_id:
                user_id = request.env['res.users'].search([("partner_id", '=', saleperson_exist_id.id)], limit=1)
                return user_id.id
        return False

    def create_delivery_address(self, data, state_id, country_id):
        return request.env['res.partner'].create({
            'name': data.get('parent_name'),
            'type': 'delivery',
            'email': data.get('customer_email'),
            'phone': data.get('customer_phone'),
            'city': data.get('city'),
            'state_id': state_id["state_id"],
            'zip': data.get('zip'),
            'country_id': country_id["country_id"],
            'company_id': data.get('company_id')
        })

    def get_payment_term_b2b(self, data):
        payment_term = data.get('payment_term')
        if payment_term:
            company = data.get('company_id')
            if 'source' in data and data.get('source'):
                company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1).id
            payment_term_exist = request.env['account.payment.term'].search(
                [("b2b_code", '=', payment_term), ("company_id", '=', company)], limit=1)
            if payment_term_exist:
                return payment_term_exist.id
        return False

    def prepare_partner_vals(self, data, country_id, state_id, datejde_object, parent_id, delivery_address,
                             sale_person_id):
        product_pricelist = request.env['product.pricelist'].sudo().search([('name', '=', data.get('price_list'))],
                                                                           limit=1)
        company = False
        if 'source' in data and data.get('source'):
            company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)
        ksa_location_id = False
        if 'ksa_location' in data and data.get('ksa_location'):
            ksa_location_id = request.env['stock.location'].sudo().search(
                [('ksa_location', '=', data.get('ksa_location'))], limit=1)

        vals = {
            'customer_type': data.get('customer_type'),
            'customer_mailing_name': data.get('customer_mailing_name'),
            'name': data.get('customer_name'),
            'email': data.get('customer_email'),
            'phone': data.get('customer_phone'),
            'vat': data.get('customer_tax_id'),
            'city': data.get('city'),
            'company_id': company.id if company else data.get('company_id'),
            'state_id': state_id["state_id"],
            'zip': data.get('zip'),
            'type': 'delivery',
            'country_id': country_id["country_id"],
            'street': data.get('addressline1'),
            'street2': data.get('addressline2'),
            'b2b_customer_id': data.get('b2b_customer_id'),
            'customer_group': data.get('customer_group'),
            'customer_group_name': data.get('customer_group_name'),
            'customer_channel': data.get('customer_channel'),
            'customer_channel_name': data.get('customer_channel_name'),
            'customer_area': data.get('customer_area'),
            'customer_area_name': data.get('customer_area_name'),
            'customer_subarea': data.get('customer_subarea'),
            'customer_subarea_name': data.get('customer_subarea_name'),
            'timestamp_jde': datejde_object,
            'active': False if data.get('customer_status') else True,
            'create_via_api': True,
            'create_b2b_owner': "Transmed-b2b",
            'user_id': sale_person_id,
            'parent_id': parent_id,
            'is_company': data.get('is_company'),
            'property_product_pricelist': product_pricelist.id if product_pricelist else None,
            'partner_latitude': data.get('partner_latitude'),
            'partner_longitude': data.get('partner_longitude'),
        }
        # customer_location_id is defined in custom_website, which depends on this module.
        if 'customer_location_id' in request.env['res.partner']._fields:
            vals['customer_location_id'] = ksa_location_id.id if ksa_location_id else None

        if delivery_address:
            vals['child_ids'] = [Command.set([delivery_address.id])]
        return vals

    @http.route('/api/partners', type='jsonrpc', auth='user', methods=['PUT'], csrf=False)
    def edit_customer_api(self, **post):
        try:

            data = post
            customer = self.find_customer_by_b2b_id(data.get('b2b_customer_id'))

            if not customer:
                return self.create_response(False, None, 'Customer Not Found', 404)

            partner = self.update_partner(customer, data)

            if isinstance(partner, dict):
                return partner
            elif hasattr(partner, 'id'):
                return self.create_response(True, {'customer_name': partner.name}, 'Customer Updated', 200)
            else:
                return self.create_response(False, {"customer": customer}, 'Customer data Error', 400)

        except Exception as e:
            return {'error': str(e)}

    def update_partner(self, customer, data):
        try:
            # Roll back partial writes: errors are returned to JDE, not raised,
            # so the request transaction would otherwise be committed.
            with request.env.cr.savepoint():
                country_id = self.get_country_id(data)
                state_id = self.get_state_id(data)
                datejde_object = self.parse_date(data.get('timestamp_jde'))
                parent_exit = 0
                parent_data = data.get('parent_id')
                sale_person_id = self.get_saleperson_id(data)

                if parent_data:
                    parent_exit_id = self.get_parent_id(data)

                    if not parent_exit_id:
                        return self.create_response(
                            False,
                            {"parent_id": parent_exit_id},
                            'parent_id not exist',
                            400
                        )

                    else:
                        parent_exit = parent_exit_id

                vals = self.prepare_partner_vals(data, country_id, state_id, datejde_object,
                                                 parent_exit, None, sale_person_id)

                portal_users = request.env['res.users'].with_context(active_test=False).search(
                    [('partner_id', '=', customer.id)]).filtered(lambda u: u._is_portal())
                if portal_users:
                    portal_users.write({'active': vals.get('active')})

                filtered_vals = {k: v for k, v in vals.items() if v is not None}
                # active_test=True so core's "linked active users" check on archiving
                # ignores the portal users archived just above.
                customer.with_context(active_test=True).write(filtered_vals)
                if 'payment_term' in data:
                    customer.with_company(customer.company_id).property_payment_term_id = self.get_payment_term_b2b(data)

                return customer

        except Exception as e:
            _logger.info(e)
            return {'error': str(e)}

    def create_response(self, success, response, message, status):
        return {'success': success, 'response': response, 'message': message, 'status': status}
