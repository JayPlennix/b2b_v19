import logging
import time
from datetime import datetime, timedelta

import requests

from odoo import Command, api, fields, models

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 120


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[
        ('jde_confirmed', 'JDE Confirmed'),
    ], ondelete={'jde_confirmed': 'set default'})

    jde_amount_untaxed = fields.Monetary(string="JDE Untaxed Amount", store=True, compute='_jde_compute_amounts')
    jde_amount_tax = fields.Monetary(string="JDE Taxes", store=True, compute='_jde_compute_amounts')
    jde_amount_total = fields.Monetary(string="JDE Total", store=True, compute='_jde_compute_amounts')
    jde_delivery_charge = fields.Monetary(string="JDE Delivery Charge", store=True, compute='_jde_compute_amounts')
    jde_invoice_no = fields.Char(string="JDE Invoice No.")

    def _ksa_delivery_date(self, start):
        """ KSA orders are delivered two days after the order date, on the next
        delivery day allowed by the customer's delivery schedule. """
        self.ensure_one()
        date = start + timedelta(days=2)
        allow_days = []
        # delivery.scheduler comes from delivery_scheduler, which depends on this module.
        if 'delivery.scheduler' in self.env:
            allow_days = self.env['delivery.scheduler'].sudo().search(
                [('customer_id', 'in', self.partner_id.ids)]).mapped('day_ids.name')
        if allow_days:
            while date.strftime("%A") not in allow_days:
                date += timedelta(days=1)
        return date

    def _compute_expected_date(self):
        ksa_orders = self.filtered(lambda o: o.state != 'cancel' and o.company_id.is_ksa and o.date_order)
        super(SaleOrder, self - ksa_orders)._compute_expected_date()
        for order in ksa_orders:
            order.expected_date = order._ksa_delivery_date(order.date_order)

    @api.depends('company_id', 'date_order', 'partner_id')
    def _compute_validity_date(self):
        ksa_orders = self.filtered(lambda o: o.company_id.is_ksa and o.date_order)
        super(SaleOrder, self - ksa_orders)._compute_validity_date()
        for order in ksa_orders:
            order.validity_date = order._ksa_delivery_date(order.date_order)

    @api.depends('order_line.jde_price_total', 'order_line.jde_delivery_charge', 'order_line.is_reward_line')
    def _jde_compute_amounts(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            wallet_price = sum(order.order_line.filtered(lambda x: x.is_reward_line).mapped('price_unit'))
            jde_delivery_charge = 0
            if order_lines.mapped('jde_delivery_charge'):
                jde_delivery_charge = max(order_lines.mapped('jde_delivery_charge'))
            order.jde_delivery_charge = jde_delivery_charge
            order.jde_amount_tax = sum(
                line.jde_price_total * ((line.jde_line_tax_rate or 5) / 100.0)
                for line in order_lines
            )
            order.jde_amount_total = (sum(order_lines.mapped('jde_price_total')) + order.jde_delivery_charge
                                      + order.jde_amount_tax - abs(wallet_price))
            order.jde_amount_untaxed = sum(order_lines.mapped('jde_price_total')) - abs(wallet_price)

    @api.depends('partner_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            partner = order.partner_id.parent_id or order.partner_id
            order.partner_invoice_id = partner.address_get(['invoice'])['invoice'] if partner else False

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.state == 'sale':
                order.create_sale_order_jde_api()
                if not order.company_id.is_jordan:
                    time.sleep(15)
                    order._confirmed_sale_oder_jde()
        return res

    def action_jde_confirm(self):
        if self.state == 'sale':
            self.create_sale_order_jde_api()
            if not self.company_id.is_jordan:
                time.sleep(15)
                self._confirmed_sale_oder_jde()

    def create_sale_order_jde_api(self, retry_count=2):
        company = self.company_id
        sale_order_create_url = company.sale_order_create_url
        if not sale_order_create_url:
            _logger.warning("JDE order creation skipped for %s: no JDE Create Saleorder Url on %s",
                            self.name, company.name)
            return False
        try:
            # A JDE outage must not prevent confirming an order the customer has paid.
            auth_token = company.get_jde_token()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            _logger.error("Error Create SaleOrder JDE for %s: cannot get a JDE token: %s", self.name, e)
            return False

        headers = {
            'Content-Type': 'application/json',
        }

        payload = {
            "token": auth_token,
            "SoldTo": self.partner_invoice_id.b2b_customer_id,
            "ShipTo": self.partner_shipping_id.b2b_customer_id,
        }

        if self.company_id.is_jordan:
            payload.update({
                "Order Number": self.name,
                "BranchPlant": "5201",
                "Company": "00101",
                "PortalReference": self.name,
                "P4210_Version": "JD039",
                "P5642230_Version": "JD001",
            })
        else:
            payload.update({
                "CustomerPO": self.name,
                "P55TMC02_Version": "TM001",
                "DeliveryInstruction": str(self.commitment_date.date().isoformat()) if self.commitment_date else ""
            })

        if company.is_ksa:
            payload.update({'BranchPlant': self.partner_id.customer_location_id.ksa_location_code
                            if self.partner_id.customer_location_id else False})

        grid_data = []
        for line in self.order_line.filtered(lambda x: not x.is_delivery and not x.is_reward_line):
            quantity, uom = line._get_jde_quantity_and_uom()
            if self.company_id.is_jordan:
                grid_data.append({
                    "Item": line.product_template_id.jde_product_id,
                    "Qty": quantity,
                    "UOM": uom.name,
                })
            else:
                grid_data.append({
                    "ItemNumber": line.product_template_id.jde_product_id,
                    "QuantityOrdered": quantity,
                    "UM": uom.name,
                    "ItemType": line.item_type if line.item_type else ""
                })
        if self.company_id.is_jordan:
            payload.update({
                "GridData_Details": grid_data,
                "Salesman": "4994",
            })
        else:
            payload.update({"GridData": grid_data})
        attempt = 0
        _logger.info("Create SaleOrder payload: %s", payload)
        while attempt < retry_count:
            try:
                response = requests.post(sale_order_create_url, headers=headers, json=payload,
                                         timeout=JDE_REQUEST_TIMEOUT)
                integration_record = self.env['integration.log'].sudo().create({
                    'name': 'Create JDE Order API',
                    'url': str(sale_order_create_url),
                    'headers': str(headers),
                    'payload': str(payload),
                })
                if response.status_code == 200:
                    integration_record.write({'response': str(response.json())})
                    response_data = response.json()
                elif response.status_code == 502:
                    integration_record.write({'response': str(response.text)})
                    response_data = []
                else:
                    integration_record.write({'response': str(response.json())})
                    response_data = response.json()
                self.env.cr.commit()

                if self.company_id.is_jordan:
                    rowset = response_data.get("SR_Portal_SearchOnlineOrder_1", {}).get("rowset", [])

                    for row in rowset:
                        if row.get('Item Number') != 'null':
                            row['Order No.'] = response_data.get('Order Number')

                    valid_rows = [row for row in rowset if row.get('Item Number') != 'null']

                    if valid_rows:
                        self.duplicate_delivery_note(valid_rows)

                _logger.info("Create SaleOrder JDE Successfully: %s", payload)

                self.logout_token(auth_token, company)

                return True

            except requests.exceptions.RequestException as e:
                _logger.info("Error Create SaleOrder JDE (Attempt %d): %s", attempt + 1, e)
                attempt += 1
                if attempt < retry_count:
                    time.sleep(2)

        _logger.error("Failed to create SaleOrder JDE after %d attempts: %s", retry_count, payload)
        return False

    def _fetch_order_status_from_jde(self, auth_token, url, company):
        try:
            sale_order_status_url = url
            dta_schemaname = company.dta_schemaname
            last_timestamp_dt = company.jde_last_status_integration_timestamp or (datetime.now() - timedelta(days=1))
            last_timestamp_str = last_timestamp_dt.strftime("%m/%d/%Y %H:%M:%S")

            payload = {
                "token": auth_token,
                "DTA_SchemaName": dta_schemaname or "CRPDTA",
                "LASTINTEGRATIONTIMESTAMP": datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            }

            if company.is_jordan:
                payload.update({
                    "LASTINTEGRATIONTIMESTAMP": last_timestamp_str
                })
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(sale_order_status_url, headers=headers, json=payload,
                                     timeout=JDE_REQUEST_TIMEOUT)
            integration_record = self.env['integration.log'].sudo().create({
                'name': 'JDE Update Sale Order Status',
                'url': str(sale_order_status_url),
                'headers': str(headers),
                'payload': str(payload),
            })

            if response.status_code == 200:
                integration_record.write({'response': str(response.json())})
                r = response.json()
            elif response.status_code == 502:
                integration_record.write({'response': str(response.text)})
                r = response.text
            else:
                integration_record.write({'response': str(response.json())})
                r = response.json()
            self.env.cr.commit()
            return r

        except requests.exceptions.RequestException as e:
            _logger.error("Error updating JDE Sale Order Status: %s", e)

    def _map_jde_status_to_odoo(self, jde_status):
        status_mapping = {
            'Customer Service': 'customer_service',
            'Credit Control': 'credit_control',
            'Order at WH': 'order_at_WH',
            'Order Confirmed': 'order_confirmed',
            'Ready To Ship': 'ready_to_ship',
            'Invoice Printed': 'invoice_printed',
            'Shipped Complete': 'shipped_complete',
            'Order Complete': 'order_complete',
            'Cancelled': 'cancel'
        }
        return status_mapping.get(jde_status)

    # scheduler function call every 10 min
    def update_saleorder_status(self):
        for company in self.env['res.company'].sudo().search([]):
            if company.sale_order_status_url:
                auth_token = company.get_jde_token()
                sale_order_status_url = company.sale_order_status_url
                try:
                    response_data = self._fetch_order_status_from_jde(auth_token, sale_order_status_url, company)
                    sale_orders = self.search([('state', 'not in', ['draft', 'sent']), ('company_id', '=', company.id)])
                    updates = []

                    if response_data and 'rows' in response_data:
                        for rec in sale_orders:

                            if company.is_jordan:
                                matching_jde_data = [jde_data for jde_data in response_data.get("rows") if
                                                     rec.name == jde_data["B2B_LPO"].strip()]
                            else:
                                matching_jde_data = [jde_data for jde_data in response_data.get("rows") if
                                                     rec.name == jde_data["B2B_LPO"].strip()
                                                     and '.' not in jde_data['LINENO']]
                            is_any_printed_status_check = any(
                                [jde_data['STATUS'] == 'Invoice Printed' for jde_data in matching_jde_data if
                                 rec.name == jde_data["B2B_LPO"].strip()])

                            is_all_cancelled_check = all(
                                [jde_data['STATUS'] == 'Cancelled' for jde_data in matching_jde_data if
                                 rec.name == jde_data["B2B_LPO"].strip()])

                            for matching_jde in matching_jde_data:
                                stock_picking = self.env['stock.picking'].search(
                                    [('sale_id', '=', rec.id), ('state', '!=', 'done'),
                                     ('carrier_tracking_ref', '=', matching_jde['ORDERNUMBER'])])
                                for pick in stock_picking:
                                    if pick.jde_state != matching_jde['STATUS']:
                                        if matching_jde['STATUS'] == 'Cancelled' and not is_all_cancelled_check:
                                            pass
                                        else:
                                            updates.append(pick.id)
                                            pick.update({'jde_state': self._map_jde_status_to_odoo(matching_jde["STATUS"])})
                                            if 'ORDERTYPE' in matching_jde:
                                                pick.update({'order_type': matching_jde['ORDERTYPE']})
                                if matching_jde.get('STATUS') != 'Cancelled':
                                    company.jde_last_status_integration_timestamp = datetime.strptime(
                                        matching_jde.get("TIMESTAMP"),
                                        '%m/%d/%Y %H:%M:%S')

                            if is_any_printed_status_check:
                                self._delivery_note_is_invoice_printed(rec)

                            all_pick_with_done_cancel = True
                            any_pick_done = False
                            for picking in rec.picking_ids:
                                if picking.state not in ['done', 'cancel'] and picking.jde_state not in ['cancel', 'invoice_printed']:
                                    all_pick_with_done_cancel = False
                                if picking.state in ['done'] and picking.jde_state in ['invoice_printed']:
                                    any_pick_done = True

                            if any_pick_done and all_pick_with_done_cancel and not rec.payment_done:
                                rec.recuring_payment()

                        _logger.info("JDE Delivery Note Status updated for %d Delivery Notes.", len(updates))

                        self.logout_token(auth_token, company)

                except Exception as e:
                    _logger.error("Error updating JDE Sale Order Scheduler: %s", e)

    def logout_token(self, auth_token, company):
        headers = {
            'Content-Type': 'application/json',
        }
        logout_url = company.jde_logout_url
        payload_logout = {"token": auth_token}
        requests.post(logout_url, headers=headers, json=payload_logout, timeout=JDE_REQUEST_TIMEOUT)
        return

    # fetch invoice generation in jde
    def _fetch_delivery_note_invoice_from_jde(self, company):
        try:
            auth_token = company.get_jde_token()
            sale_order_invoiced_url = company.sale_order_jde_invoiced_url
            dta_schemaname = company.dta_schemaname

            last_timestamp_dt = company.jde_last_invoiced_integration_timestamp or (datetime.now() - timedelta(days=1))
            last_timestamp_str = last_timestamp_dt.strftime("%m/%d/%Y %H:%M:%S")

            payload = {
                "token": auth_token,
                "DTA_SchemaName": dta_schemaname or "CRPDTA",
                "LASTINTEGRATIONTIMESTAMP": last_timestamp_str
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(sale_order_invoiced_url, headers=headers, json=payload,
                                     timeout=JDE_REQUEST_TIMEOUT)
            integration_record = self.env['integration.log'].sudo().create({
                'name': 'JDE Fetch Delivery Note Invoice',
                'url': str(sale_order_invoiced_url),
                'headers': str(headers),
                'payload': str(payload),
            })
            if response.status_code == 200:
                integration_record.write({'response': str(response.json())})
                r = response.json()
            elif response.status_code == 502:
                integration_record.write({'response': str(response.text)})
                r = response.text
            else:
                integration_record.write({'response': str(response.json())})
                r = response.json()
            self.env.cr.commit()
            return r

        except requests.exceptions.RequestException as e:
            _logger.error("Error updating JDE Delivery Note: %s", e)

    def _set_jde_line_values(self, sale_line, jde_price_total, jde_price_unit, jde_delivery_charge,
                             jde_line_tax_rate, invoice_no):
        if not sale_line:
            return
        sale_line.jde_price_total = jde_price_total
        sale_line.jde_line_tax_rate = jde_line_tax_rate
        sale_line.jde_delivery_charge = jde_delivery_charge
        sale_line.jde_price_unit = jde_price_unit
        if invoice_no:
            sale_line.order_id.jde_invoice_no = invoice_no

    # Updating the delivery note in odoo
    def _delivery_note_is_invoice_printed(self, sale_order):
        try:
            stock_picking = sale_order.picking_ids.filtered(lambda x: x.state != 'done')
            company = sale_order.company_id
            response_data = self._fetch_delivery_note_invoice_from_jde(company)

            product_details = [jde_data for jde_data in response_data.get("rows", [])
                               if sale_order.name == jde_data["B2B_LPO"].strip() and '.' not in jde_data['LINENO']]
            _logger.info("Delivery Note Res : %s", product_details)
            for product in product_details:
                invoice_no = False
                product_id = product.get("ITEM_NUMBER").strip()
                track_no = product.get("ORDER_NUMBER").strip()
                sl_no_comp = int(product.get("LINENO").strip())
                jde_quantity = float(product.get("QUANTITY"))
                jde_price_total = float(product.get("EXTENDED_PRICE").strip())
                jde_price_unit = float(product.get("UNIT_PRICE").strip())
                jde_delivery_charge = (float(product.get('DELIVERY_CHARGE').strip())
                                       if product.get('DELIVERY_CHARGE').strip() != 'null' else 0.0)
                jde_line_tax_rate = 5
                if 'LINE_TAX_RATE' in product:
                    jde_line_tax_rate = int(product.get('LINE_TAX_RATE').strip())
                if 'INVOICE_NO' in product and product.get("INVOICE_NO").strip():
                    if product.get("INVOICE_NO").strip().isdigit():
                        invoice_no = int(product.get("INVOICE_NO").strip()) or False
                jde_values = (jde_price_total, jde_price_unit, jde_delivery_charge, jde_line_tax_rate, invoice_no)
                for stock in stock_picking:
                    if stock.carrier_tracking_ref != track_no:
                        continue
                    for move in stock.move_ids:
                        # JDE quantities are in the product's unit.
                        quantity = move.product_id.uom_id._compute_quantity(jde_quantity, move.product_uom)
                        if move.move_line_ids:
                            operation = move.move_line_ids[0]
                            if stock.company_id.is_ksa:
                                lot_id = self.env['stock.lot'].search(
                                    [('product_id', '=', operation.product_id.id), ('name', '=', product_id),
                                     ('company_id', '=', stock.company_id.id)])
                                if operation.sl_no_comp == sl_no_comp:
                                    self._set_jde_line_values(operation.move_id.sale_line_id, *jde_values)
                                    if lot_id:
                                        operation.lot_id = lot_id
                                        operation.quantity = quantity
                                    elif operation.product_id.product_tmpl_id.jde_product_id == product_id:
                                        operation.quantity = quantity
                            else:
                                if (operation.product_id.product_tmpl_id.jde_product_id == product_id
                                        and operation.sl_no_comp == sl_no_comp):
                                    self._set_jde_line_values(operation.move_id.sale_line_id, *jde_values)
                                    operation.quantity = quantity
                        else:
                            if move.product_id.product_tmpl_id.jde_product_id == product_id:
                                move_line_vals = move._prepare_move_line_vals(quantity=quantity)
                                self._set_jde_line_values(move.sale_line_id, *jde_values)
                                move_line_vals.update({'sl_no_comp': sl_no_comp})
                                move.write({'move_line_ids': [Command.create(move_line_vals)]})

                    if stock.state in ['assigned', 'confirmed', 'waiting']:
                        stock_ctx = stock.with_context(button_validate_picking_ids=stock.ids)
                        res = stock_ctx._pre_action_done_hook()
                        if res is not True:
                            backorder_confirmation_obj = self.env['stock.backorder.confirmation'].sudo().with_context(
                                stock_ctx.env.context).create({
                                    'show_transfers': False, 'pick_ids': [Command.link(p.id) for p in stock]})
                            if backorder_confirmation_obj:
                                backorder_confirmation_obj.with_context(validate_from_api=True).process_cancel_backorder()
                        else:
                            stock.with_context(validate_from_api=True).button_validate()
                        if stock.state in ['done', 'cancel']:
                            if stock.move_ids and not any(stock.move_ids.mapped('quantity')):
                                stock.jde_state = 'cancel'

            _logger.info("Invoiced Delivery note updated successfully.")
        except Exception as e:
            _logger.error("Error updating JDE Invoiced delivery note: %s", e)

    # -------------------------------------------------------------------------
    # eCommerce cart
    # -------------------------------------------------------------------------

    def _compute_cart_info(self):
        # The cart icon counts products (lines), not units: with packagings converted to
        # units, 2 boxes of 12 would otherwise show 24.
        super()._compute_cart_info()
        for order in self:
            order.cart_quantity = len(order.website_order_line.filtered(
                lambda line: not line.is_delivery and not line.is_reward_line))

    def _cart_add(self, product_id, quantity=1.0, *, uom_id=None, **kwargs):
        # Packagings are sold in the product's unit, as JDE expects (2 x BOX of 12 = 24 units).
        product = self.env['product.product'].browse(product_id)
        if uom_id:
            uom = self.env['uom.uom'].browse(uom_id)
            if uom in product.uom_ids:
                quantity = uom._compute_quantity(quantity, product.uom_id)
                uom_id = product.uom_id.id

        values = super()._cart_add(product_id, quantity, uom_id=uom_id, **kwargs)

        order_line = self.order_line.filtered(lambda line: line.id == values.get('line_id'))
        if order_line:
            item_type = kwargs.get('productItemOption') or False
            order_line.item_type = item_type
            no_of_piece = int(kwargs.get('quantityPieces') or 1)
            if item_type and quantity > 0 and no_of_piece > 1:
                for _i in range(no_of_piece - 1):
                    order_line.copy({
                        'order_id': self.id,
                        'product_uom_qty': order_line.product_uom_qty,
                        'item_type': item_type,
                    })
        return values

    def _cart_find_product_line(self, product_id, uom_id, linked_line_id=False,
                                no_variant_attribute_value_ids=None, **kwargs):
        # Sliced / shredded items are always added as separate lines, and plain items
        # are never merged into a sliced / shredded line.
        if kwargs.get('productItemOption'):
            return self.env['sale.order.line']
        lines = super()._cart_find_product_line(
            product_id, uom_id, linked_line_id=linked_line_id,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids, **kwargs)
        return lines.filtered(lambda line: not line.item_type)

    # -------------------------------------------------------------------------

    def duplicate_delivery_note(self, valid_rows):
        picking = self.env['stock.picking'].search([('sale_id', '=', self.id), ('picking_type_code', '=', 'outgoing')])
        move_lines = picking.move_ids
        products = move_lines.mapped('product_id')
        for product in products:
            new_picking = False
            for item in valid_rows:
                order_no = item["Order No."]
                if self.company_id.is_jordan:
                    item_no = item["Item Number"]
                else:
                    item_no = item["2nd Item Number"]
                if product.jde_product_id == item_no:
                    new_picking = self.env['stock.picking'].search(
                        [('carrier_tracking_ref', '=', order_no), ('origin', '=', self.name)], limit=1)

            if not new_picking:
                new_picking = picking.copy()
            product_move_lines = move_lines.filtered(lambda m: m.product_id == product)

            if not new_picking.carrier_tracking_ref:
                new_picking.move_ids.unlink()

            for line in product_move_lines:
                line.copy({
                    'picking_id': new_picking.id,
                })
            for item in valid_rows:
                order_no = item["Order No."]
                if self.company_id.is_jordan:
                    item_no = item["Item Number"]
                else:
                    item_no = item["2nd Item Number"]
                if new_picking.move_ids and new_picking.move_ids[0].product_id.jde_product_id == item_no:
                    new_picking.write({
                        'carrier_tracking_ref': order_no,
                    })
            new_picking.action_confirm()
            i = 0
            for item in valid_rows:
                i = i + 1
                if self.company_id.is_jordan:
                    item_no = item["Item Number"]
                else:
                    item_no = item["2nd Item Number"]
                # JDE quantities are in the product's unit.
                quantity = float(item["Quantity"])
                lineno = int(item["Line Number"]) if 'Line Number' in item else i
                jde_price_total = float(item["Extended Price"])
                if "UNIT_PRICE" in item:
                    jde_price_unit = float(item["UNIT_PRICE"])
                else:
                    jde_price_unit = False
                for move in new_picking.move_ids:
                    if (not move.move_line_ids and move.product_id.jde_product_id == item_no
                            and move.product_qty == quantity):
                        move_line_vals = move._prepare_move_line_vals(
                            quantity=move.product_id.uom_id._compute_quantity(quantity, move.product_uom))
                        move_line_vals.update({'sl_no_comp': lineno, 'is_sl_no_comp': True})
                        move.write({'move_line_ids': [Command.create(move_line_vals)]})
                        if move.sale_line_id:
                            move.sale_line_id.jde_price_total = jde_price_total
                            if not jde_price_unit:
                                move.sale_line_id.jde_price_unit = move.sale_line_id.price_unit
                            else:
                                move.sale_line_id.jde_price_unit = jde_price_unit
                        break

                for line in new_picking.move_line_ids:
                    if (line.product_id.jde_product_id == item_no and line.move_id.product_qty == quantity
                            and not line.is_sl_no_comp):
                        if line.move_id.sale_line_id:
                            line.move_id.sale_line_id.jde_price_total = jde_price_total
                            if not jde_price_unit:
                                line.move_id.sale_line_id.jde_price_unit = line.move_id.sale_line_id.price_unit
                            else:
                                line.move_id.sale_line_id.jde_price_unit = jde_price_unit
                        line.write({'sl_no_comp': lineno, 'is_sl_no_comp': True})
                        break

        self.state = 'jde_confirmed'
        picking.unlink()
        return

    def _confirmed_sale_oder_jde(self):
        try:
            company = self.company_id
            auth_token = company.get_jde_token()
            search_by_reference_url = company.search_by_reference_url

            payload = {
                "token": auth_token,
                "Reference": self.name,
                "P5542231_Version": "TMD01"
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(search_by_reference_url, headers=headers, json=payload,
                                     timeout=JDE_REQUEST_TIMEOUT)
            integration_record = self.env['integration.log'].sudo().create({
                'name': 'JDE Confirmed Sale Order',
                'url': str(search_by_reference_url),
                'headers': str(headers),
                'payload': str(payload),
            })
            if response.status_code == 200:
                integration_record.write({'response': str(response.json())})
                response_data = response.json()
            elif response.status_code == 502:
                integration_record.write({'response': str(response.text)})
                response_data = []
            else:
                integration_record.write({'response': str(response.json())})
                response_data = response.json()
            self.env.cr.commit()
            rowset = response_data.get("Result", {}).get("rowset", [])
            valid_rows = [row for row in rowset if row.get("Order No.", 0) != 0]

            if valid_rows:
                self.duplicate_delivery_note(valid_rows)

        except requests.exceptions.RequestException as e:
            _logger.error("Error updating JDE Delivery Note: %s", e)
        except Exception as e:
            _logger.error("Unexpected error in _confirmed_sale_oder_jde: %s", e)
