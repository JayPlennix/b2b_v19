import logging
from datetime import datetime

from odoo import Command, http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _is_ksa(company):
    # res.company.is_ksa is defined in custom_website, which depends on this module.
    return bool(company) and 'is_ksa' in company._fields and company.is_ksa


def _is_jordan(company):
    return bool(company) and 'is_jordan' in company._fields and company.is_jordan


class ProductAPI(http.Controller):

    @http.route('/api/product', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_product_api(self, **post):
        try:
            datas = post.get('data')
            product_create_lst = []
            product_dict = {}
            _logger.info(datas)
            for data in datas:
                jde_product_id = data.get('product_id')
                if '.' in str(jde_product_id):
                    lot_product_data = int(str(jde_product_id).split('.')[0])
                else:
                    lot_product_data = jde_product_id
                product_items_exist = self.find_product_by_jde_code(lot_product_data)

                if not product_items_exist:
                    product = self.create_product(data)

                    if isinstance(product, dict):
                        product_dict = product
                        break

                    if hasattr(product, 'id'):
                        product_create_lst.append(product.id)

                else:
                    if 'source' in data and data.get('source') and data.get('source') == 'KSA':
                        self.create_lot(data)
                    else:
                        location = self.get_location_id(data)
                        quantity = data.get("quantity")
                        product_id = request.env['product.product'].search(
                            [("product_tmpl_id", '=', product_items_exist.id)], limit=1)
                        if product_id and quantity and location:
                            stock_quants = request.env['stock.quant']
                            stock_quants._update_available_quantity(product_id, location, quantity)

            if product_dict:
                return product_dict

            if product_create_lst:
                return self.create_response(True,
                                            {'products': product_create_lst},
                                            'Products Created', 200)
            else:
                return self.create_response(False,
                                            {"products": product_create_lst},
                                            'Product data Error', 400)

        except Exception as e:
            _logger.info(e)
            return {'error': str(e)}

    def find_product_by_jde_code(self, jde_product_id):
        return request.env['product.template'].with_context(active_test=False).search(
            [("jde_product_id", '=', jde_product_id)], limit=1)

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

    def get_country_id(self, data):
        try:
            country = data.get('origin_of_goods')
            if not country:
                return {"country_id": False}

            country_id = request.env['res.country'].search(
                ['|', ("name", 'ilike', country), ("code", 'ilike', country)], limit=1)
            return {"country_id": country_id.id if country_id else False}

        except Exception as e:
            _logger.error('Error in get_country_id: %s', e)
            return {'error': str(e)}

    def create_product(self, data):
        try:
            # Roll back partial writes: errors are returned to JDE, not raised,
            # so the request transaction would otherwise be committed.
            with request.env.cr.savepoint():
                datejde_object = self.parse_date(data.get('timestamp_jde'))
                country_id = self.get_country_id(data)
                website_category = self.get_website_category(data)
                product_category = self.get_product_category(data)
                vals = self.prepare_product_vals(data, datejde_object, country_id, product_category,
                                                 website_category)
                location = self.get_location_id(data)
                product = request.env['product.template'].create(vals)
                if not product.active:
                    for variant in product.product_variant_ids:
                        variant.write({'active': False})
                else:
                    for variant in product.product_variant_ids:
                        variant.write({'active': True})
                quantity = data.get("quantity")
                self.update_attribute_values(data, product_id=product)
                self.create_product_package(data, product)
                product_id = request.env['product.product'].search([("product_tmpl_id", '=', product.id)], limit=1)

                if 'source' in data and data.get('source') and data.get('source') == 'KSA':
                    self.create_lot(data)
                else:
                    if product_id and quantity and location:
                        stock_quants = request.env['stock.quant']
                        stock_quants._update_available_quantity(product_id, location, quantity)
                return product

        except Exception as e:
            return {'error': str(e)}

    def get_website_category(self, data):
        try:
            list_category_list = []
            website_category = data.get('website_category', '').strip()

            company = request.env['res.company'].browse(data.get('company_id'))
            if 'source' in data and data.get('source'):
                company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)
            jde_product_id = data.get('product_id')
            if '.' in str(jde_product_id):
                lot_product_data = int(str(jde_product_id).split('.')[0])
            else:
                lot_product_data = jde_product_id
            product_items_exist = self.find_product_by_jde_code(lot_product_data)
            if product_items_exist and product_items_exist.company_id:
                company = product_items_exist.company_id

            website = request.env['website'].search([('company_id', '=', company.id)], limit=1)

            if website_category:
                website_category_id = request.env['product.public.category'].search(
                    [("name", '=', website_category), ('website_id', '=', website.id)], limit=1)

                if website_category_id:
                    list_category_list.append(website_category_id.id)
                else:
                    parent_name = data.get('product_category', '').strip()

                    if parent_name:
                        website_parent_category = request.env['product.public.category'].search(
                            [("name", '=', parent_name), ('website_id', '=', website.id)], limit=1)

                        if not website_parent_category:
                            website_parent_category = request.env['product.public.category'].sudo().create(
                                {'name': parent_name, 'website_id': website.id})

                        new_website_category = request.env['product.public.category'].sudo().create(
                            {'name': website_category, 'parent_id': website_parent_category.id,
                             'website_id': website.id})
                        list_category_list.append(new_website_category.id)
            else:
                product_category = data.get('product_category', '').strip()
                website_category_id = request.env['product.public.category'].search(
                    [("name", '=', product_category), ('website_id', '=', website.id)], limit=1)
                if website_category_id:
                    list_category_list.append(website_category_id.id)
                else:
                    new_website_category = request.env['product.public.category'].sudo().create(
                        {'name': product_category, 'website_id': website.id})
                    list_category_list.append(new_website_category.id)

            return list_category_list

        except Exception as e:
            _logger.error('Error in get_website_category: %s', e)
            return {'error': str(e)}

    def get_location_id(self, data):
        jde_product_id = data.get('product_id')

        company_id = False
        if 'company_id' in data:
            company_id = data.get('company_id')
            company = False
            if 'source' in data and data.get('source'):
                company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)
            if company:
                company_id = company.id
        else:
            if '.' in str(jde_product_id):
                lot_product_data = int(str(jde_product_id).split('.')[0])
            else:
                lot_product_data = jde_product_id
            product_items_exist = self.find_product_by_jde_code(lot_product_data)
            company_id = product_items_exist.company_id.id

        location = data.get("location")
        location_id = request.env['stock.location'].search([
            ("complete_name", '=', location),
            ("company_id", '=', company_id)
        ], limit=1)
        if not location_id:
            raise ValueError(f"Location '{location}' not found for company ID {company_id}")
        return location_id

    def get_tax_id(self, data):
        company = request.env['res.company'].browse(data.get('company_id'))
        if 'source' in data and data.get('source'):
            company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)
        customer_tax_id = data.get('customer_tax')
        tax_id = request.env['account.tax'].sudo()
        if customer_tax_id == "Y":
            tax_id = request.env['account.tax'].sudo().search([("active", '=', 1), ('company_id', '=', company.id)],
                                                              limit=1)
        return tax_id

    def prepare_product_vals(self, data, datejde_object, country_id, product_category, website_category):
        uom = data.get("uom")

        company = request.env['res.company'].browse(data.get('company_id'))
        if 'source' in data and data.get('source'):
            company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)

        jde_product_id = data.get('product_id')
        if '.' in str(jde_product_id):
            lot_product_data = int(str(jde_product_id).split('.')[0])
        else:
            lot_product_data = jde_product_id
        product_items_exist = self.find_product_by_jde_code(lot_product_data)
        if product_items_exist and product_items_exist.company_id:
            company = product_items_exist.company_id

        uom_id = request.env['uom.uom'].search([("name", '=', uom)], limit=1)
        location = None
        if 'location' in data:
            location = self.get_location_id(data)
        customer_tax = None
        if 'customer_tax' in data:
            customer_tax = self.get_tax_id(data)

        if data.get("check_availability"):
            if data.get('is_ksa'):
                raise ValueError("For KSA Company availability is always 0.")

            check_availability = 1 if data.get("check_availability") == 'Y' else 0
            allow_out_of_stock_order = 0 if check_availability == 1 else 1
            show_availability = 1 if check_availability == 1 else 0
        else:
            check_availability = None
            show_availability = None
            allow_out_of_stock_order = None

        brand_id = False
        if data.get("brand_name"):
            brand_id = request.env['product.brand'].sudo().search([('name', '=', data.get("brand_name"))], limit=1)
            if not brand_id:
                brand_id = request.env['product.brand'].sudo().create({'name': data.get("brand_name")})

        jde_product_id = data.get('product_id')
        lot_product_data = data.get('product_id')
        if '.' in str(jde_product_id):
            lot_product_data = int(str(jde_product_id).split('.')[0])

        default_code = str(data.get('internal_reference'))
        if '.' in str(data.get('internal_reference')):
            default_code = int(str(data.get('internal_reference')).split('.')[0])

        active = None
        if 'can_be_sold' in data:
            active = False
            if data.get('can_be_sold'):
                active = True
        is_ksa = _is_ksa(company)
        vals = {
            'name': data.get('name'),
            'type': 'consu',
            'is_storable': True,
            'default_code': default_code,
            'jde_product_id': lot_product_data,
            'sale_ok': data.get('can_be_sold'),
            'company_id': company.id if company else data.get('company_id'),
            'uom_id': uom_id.id if uom_id else None,
            'purchase_ok': False,
            'is_published': data.get('can_be_published'),
            'standard_price': data.get('cost'),
            'list_price': data.get('sales_price'),
            'taxes_id': [Command.set([customer_tax.id])] if customer_tax else None,
            'invoice_policy': "delivery",
            'country_of_origin': country_id["country_id"],
            'public_categ_ids': [Command.set(website_category)] if website_category else None,
            'storage': data.get("storage"),
            'temperature': data.get("temperature"),
            'timestamp_jde': datejde_object,
            'product_family': data.get("product_family"),
            'product_family_name': data.get("product_family_name"),
            'jde_product_name': data.get("jde_product_name"),
            'item_type': data.get("item_type"),
            'item_type_name': data.get("item_type_name"),
            'short_item_no': data.get("short_item_no"),
            'brand': data.get("brand"),
            'brand_id': brand_id.id if brand_id else None,
            'brand_name': data.get("brand_name"),
            'brand_type': data.get("brand_type"),
            'brand_type_name': data.get("brand_type_name"),
            'supplier_code': data.get("supplier_code"),
            'supplier_name': data.get("supplier_name"),
            'categ_id': product_category[0] if product_category else None,
            'tracking': "lot" if is_ksa else "none",
            'use_expiration_date': bool(is_ksa),
            'jde_stock_location': location.id if location else None,
            "check_availability": check_availability,
            "show_availability": show_availability,
            "allow_out_of_stock_order": allow_out_of_stock_order,
            'active': active,
            'create_via_api': True
        }
        return vals

    def create_lot_with_validation(self, jde_product_id, product_id, expiration_date, internal_ref):
        lot = request.env['stock.lot'].sudo().search([
            ('name', '=', jde_product_id),
            ('product_id', '=', product_id.id),
            ('company_id', '=', product_id.company_id.id)
        ], limit=1)

        if not lot:
            lot = request.env['stock.lot'].create({
                "name": jde_product_id,
                "product_id": product_id.id,
                "company_id": product_id.company_id.id,
                "expiration_date": expiration_date,
                "ref": internal_ref,
            })
        return lot

    def create_lot(self, data):
        try:
            lot_product_data = data.get("product_id")
            quantity = data.get("quantity")
            location = data.get("location")
            lot_name = data.get("product_id")
            internal_ref = data.get("product_id")
            expiration_date = self.parse_date(data.get('expiration_date'))

            if '.' in str(data.get("product_id")):
                lot_product_data = int(str(data.get("product_id")).split('.')[0])
                lot_name = str(data.get("product_id")).split('.')[1]

            product_templat_id = request.env['product.template'].search([("jde_product_id", '=', lot_product_data)],
                                                                         limit=1)
            product_id = request.env['product.product'].search([("product_tmpl_id", '=', product_templat_id.id)],
                                                               limit=1)

            if product_id and location:
                location_id = request.env['stock.location'].search(
                    [("complete_name", '=', location), ("company_id", '=', product_id.company_id.id)], limit=1)
                lot = False
                if lot_name:
                    lot = self.create_lot_with_validation(lot_name, product_id, expiration_date, internal_ref)
                stock_quants = request.env['stock.quant']
                if quantity:
                    stock_quants._update_available_quantity(product_id, location_id, quantity, lot_id=lot)
                return lot

            return self.create_response(False, {
                'product_code': lot_product_data
            }, 'Product code not exist', 200)

        except Exception as e:
            _logger.error('Error in data_error create lot: %s', e)
            return {'error': str(e)}

    def get_product_category(self, data):
        try:
            list_category_list = []
            website_category = data.get('website_category', '').strip()

            company = request.env['res.company'].browse(data.get('company_id'))
            if 'source' in data and data.get('source'):
                company = request.env['res.company'].sudo().search([('source', '=', data.get('source'))], limit=1)

            jde_product_id = data.get('product_id')
            if '.' in str(jde_product_id):
                lot_product_data = int(str(jde_product_id).split('.')[0])
            else:
                lot_product_data = jde_product_id
            product_items_exist = self.find_product_by_jde_code(lot_product_data)
            if product_items_exist and product_items_exist.company_id:
                company = product_items_exist.company_id

            if website_category:
                website_category_id = request.env['product.category'].search(
                    [("name", '=', website_category), ('company_id', '=', company.id)], limit=1)

                if website_category_id:
                    list_category_list.append(website_category_id.id)
                else:
                    parent_name = data.get('product_category', '').strip()

                    if parent_name:
                        website_parent_category = request.env['product.category'].search(
                            [("name", '=', parent_name), ('company_id', '=', company.id)], limit=1)

                        if not website_parent_category:
                            website_parent_category = request.env['product.category'].sudo().create(
                                {'name': parent_name, 'company_id': company.id})

                        new_website_category = request.env['product.category'].sudo().create(
                            {'name': website_category, 'parent_id': website_parent_category.id,
                             'company_id': company.id})
                        list_category_list.append(new_website_category.id)
            else:
                product_category = data.get('product_category', '').strip()
                website_category_id = request.env['product.category'].search(
                    [("name", '=', product_category), ('company_id', '=', company.id)], limit=1)
                if website_category_id:
                    list_category_list.append(website_category_id.id)
                else:
                    new_website_category = request.env['product.category'].sudo().create(
                        {'name': product_category, 'company_id': company.id})
                    list_category_list.append(new_website_category.id)

            return list_category_list

        except Exception as e:
            _logger.error('Error in get_product_category: %s', e)
            return {'error': str(e)}

    def update_attribute_values(self, data, product_id):
        try:
            attribute_model = request.env['product.attribute']
            value_model = request.env['product.attribute.value']

            attribute_value_data = data.get("product_attribute_value")

            if not attribute_value_data:
                return

            updating_data = []

            for attribute_value in attribute_value_data:
                attribute_name = attribute_value.get('attribute')
                value_list = attribute_value.get('values', '').split(',')

                attribute_exist = attribute_model.search([('name', 'ilike', attribute_name)], limit=1)

                value_id_list = []

                if attribute_exist:
                    existing_value_names = attribute_exist.value_ids.mapped('name')

                    for value in value_list:
                        if value in existing_value_names:
                            value_id = value_model.search(
                                [('name', 'ilike', value), ('attribute_id', '=', attribute_exist.id)], limit=1)
                            value_id_list.append(value_id.id)
                        else:
                            value_id = value_model.create({'name': value, 'attribute_id': attribute_exist.id})
                            value_id_list.append(value_id.id)

                    updating_data.append({
                        'attribute_id': attribute_exist.id,
                        'product_tmpl_id': product_id.id,
                        'value_ids': [Command.set(value_id_list)]
                    })
                else:
                    new_attribute = attribute_model.create({'name': attribute_name})

                    for new_value in value_list:
                        value_new_id = value_model.create({'name': new_value, 'attribute_id': new_attribute.id})
                        value_id_list.append(value_new_id.id)

                    updating_data.append({
                        'attribute_id': new_attribute.id,
                        'product_tmpl_id': product_id.id,
                        'value_ids': [Command.set(value_id_list)]
                    })

            if updating_data:
                request.env['product.template.attribute.line'].create(updating_data)
        except Exception as e:
            _logger.error('Error in attribute update: %s', e)
            return {'error': str(e)}

        return

    # -------------------------------------------------------------------------
    # Packagings
    #
    # Odoo 19 has no product.packaging: packagings are units of measure defined
    # relative to another unit, listed on the product in uom_ids. Each JDE
    # package becomes such a unit, relative to the product's unit, or relative
    # to its secondary package's unit (CARTON = 10 x BOX).
    # -------------------------------------------------------------------------

    def _get_packaging_uom(self, package_name, reference_uom, factor, base_uom):
        Uom = request.env['uom.uom'].sudo()
        factor = float(factor)
        uom = Uom.search([
            ('jde_package_name', '=', package_name),
            ('relative_uom_id', '=', reference_uom.id),
            ('relative_factor', '=', factor),
        ], limit=1)
        if not uom:
            quantity = factor * reference_uom.factor / base_uom.factor
            uom = Uom.create({
                'name': f"{package_name} ({quantity:g} {base_uom.name})",
                'jde_package_name': package_name,
                'relative_uom_id': reference_uom.id,
                'relative_factor': factor,
            })
        return uom

    def _sync_product_packagings(self, data, product):
        package_details = data.get("package_details")
        if not package_details:
            return
        base_uom = product.uom_id
        # Rebuild the product's whole JDE packaging chain so that packages defined on
        # top of a changed package follow it (BOX 12 -> 6 makes CARTON = 10 x BOX 60).
        # spec: name -> (secondary package name or None, factor, fallback quantity in base units)
        current = product.uom_ids.filtered('jde_package_name')
        specs = {}
        for uom in current:
            quantity = uom.factor / base_uom.factor
            if uom.relative_uom_id in current:
                specs[uom.jde_package_name] = (uom.relative_uom_id.jde_package_name, uom.relative_factor, quantity)
            else:
                specs[uom.jde_package_name] = (None, quantity, quantity)
        for package in package_details:
            secondary_name = package.get('secondary_package')
            if secondary_name and 'secondary_quantity' in package and secondary_name != package['name']:
                specs[package['name']] = (secondary_name, package['secondary_quantity'], package['quantity'])
            else:
                specs[package['name']] = (None, package['quantity'], package['quantity'])

        resolved = {}
        pending = dict(specs)
        while pending:
            progress = False
            for name, (secondary_name, factor, quantity) in list(pending.items()):
                if secondary_name and secondary_name in pending:
                    continue  # resolve the secondary package first
                if secondary_name and secondary_name in resolved:
                    uom = self._get_packaging_uom(name, resolved[secondary_name], factor, base_uom)
                else:
                    # No secondary package, or it is unknown: use the package's own quantity.
                    uom = self._get_packaging_uom(name, base_uom, quantity, base_uom)
                resolved[name] = uom
                del pending[name]
                progress = True
            if not progress:
                # Packages referencing each other: fall back to their own quantities.
                for name, (_secondary_name, _factor, quantity) in pending.items():
                    resolved[name] = self._get_packaging_uom(name, base_uom, quantity, base_uom)
                break

        product.write({'uom_ids': [Command.unlink(uom.id) for uom in current]
                                  + [Command.link(uom.id) for uom in resolved.values()]})

    def create_product_package(self, data, product):
        try:
            self._sync_product_packagings(data, product)
        except Exception as e:
            _logger.error('Error in create_product_package: %s', e)
            return {'error': str(e)}

    def edit_product_package(self, data, product):
        try:
            self._sync_product_packagings(data, product)
        except Exception as e:
            _logger.error('Error in edit_product_package: %s', e)
            return {'error': str(e)}

    def create_response(self, success, response, message, status):
        return {'success': success, 'response': response, 'message': message, 'status': status}

    @http.route('/api/product', type='jsonrpc', auth='user', methods=['PUT'], csrf=False)
    def edit_product_api(self, **post):
        try:
            datas = post.get('data')
            product_update_lst = []
            product_dict = {}
            _logger.info(datas)
            for data in datas:
                product_id = data.get('product_id')
                if not product_id:
                    return self.create_response(False, {}, 'Product ID is required', 400)
                if '.' in str(product_id):
                    lot_product_data = int(str(product_id).split('.')[0])
                else:
                    lot_product_data = product_id
                product = self.find_product_by_jde_code(lot_product_data)

                if product:
                    product = self.update_product(data, product)

                    if isinstance(product, dict) and 'error' in product:
                        product_dict = product
                        break

                    if hasattr(product, 'id') and product.id not in product_update_lst:
                        product_update_lst.append(product.id)

            if product_dict:
                return product_dict

            if product_update_lst:
                return self.create_response(True,
                                            {'products': product_update_lst},
                                            'Product Updated', 200)
            else:
                return self.create_response(False,
                                            {"products": product_update_lst},
                                            'Item Not available', 400)
        except Exception as e:
            _logger.info(e)
            return {'error': str(e)}

    def update_product(self, data, product):
        try:
            # Roll back partial writes: errors are returned to JDE, not raised,
            # so the request transaction would otherwise be committed.
            with request.env.cr.savepoint():
                data.update({
                    'is_ksa': _is_ksa(product.company_id),
                    'is_jordan': _is_jordan(product.company_id),
                })
                datejde_object = self.parse_date(data.get('timestamp_jde'))
                country_id = self.get_country_id(data)
                website_category = self.get_website_category(data)
                product_category = self.get_product_category(data)
                vals = self.prepare_product_vals(data, datejde_object, country_id, product_category,
                                                 website_category)
                filtered_vals = {k: v for k, v in vals.items() if v is not None}
                product.write(filtered_vals)
                if not product.active:
                    for variant in product.product_variant_ids:
                        variant.write({'active': False})
                else:
                    for variant in product.product_variant_ids:
                        variant.write({'active': True})
                self.update_attribute_values(data, product_id=product)
                self.edit_product_package(data, product)
                if 'quantity' in data and 'location' in data:
                    quantity = float(data.get("quantity"))
                    location = data.get("location")
                    product_id = request.env['product.product'].search([("product_tmpl_id", '=', product.id)],
                                                                       limit=1)
                    if _is_ksa(product.company_id):
                        self.edit_lot(data)
                    else:
                        if product_id and location:
                            location_id = request.env['stock.location'].search(
                                [("complete_name", '=', location), ("company_id", '=', product_id.company_id.id)],
                                limit=1)
                            stock_quants = request.env['stock.quant']

                            stock_quant = request.env['stock.quant'].search([
                                ('product_id', '=', product_id.id),
                                ('location_id', '=', location_id.id),
                            ], limit=1)

                            if quantity:
                                if stock_quant:
                                    stock_quant.write({'quantity': quantity})
                                else:
                                    stock_quants._update_available_quantity(product_id, location_id, quantity)
                return product

        except Exception as e:
            return {'error': str(e)}

    def edit_lot(self, data):
        try:
            jde_product_id = data.get("product_id")
            quantity = data.get("quantity")
            location = data.get("location")

            lot_id = request.env['stock.lot'].search([("ref", '=', jde_product_id)], limit=1)
            if 'expiration_date' in data:
                expiration_date = self.parse_date(data.get('expiration_date'))

                if lot_id:
                    lot_id.write({'expiration_date': expiration_date})

            if lot_id and location:

                location_id = request.env['stock.location'].search(
                    [("complete_name", '=', location), ("company_id", '=', lot_id.product_id.company_id.id)], limit=1)
                stock_quants = request.env['stock.quant']

                stock_quant = request.env['stock.quant'].search([
                    ('product_id', '=', lot_id.product_id.id),
                    ('location_id', '=', location_id.id),
                    ('lot_id', '=', lot_id.id)
                ], limit=1)

                if quantity:
                    if stock_quant:
                        stock_quant.write({'quantity': quantity})
                    else:
                        stock_quants._update_available_quantity(lot_id.product_id, location_id, quantity,
                                                                lot_id=lot_id)
                return lot_id

            return self.create_response(False, {
                'product_code': jde_product_id
            }, 'Product code not exist', 200)

        except Exception as e:
            _logger.error('Error in data_error edit lot: %s', e)
            return {'error': str(e)}
