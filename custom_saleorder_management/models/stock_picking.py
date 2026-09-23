import logging
import time
from datetime import datetime

import requests

from odoo import Command, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)

JDE_REQUEST_TIMEOUT = 120


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    sl_no_comp = fields.Integer('SNO.')
    is_sl_no_comp = fields.Boolean('Is SNO.')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    grv_order_type = fields.Selection([('GS', 'GS'), ('SR', 'SR')], string='Return Order Type', readonly=True,
                                      help='Order Type For GRV Integration')
    driver = fields.Char(string="Driver", help="Driver responsible for the delivery")
    vehicle = fields.Char(string="Vehicle", help="Vehicle assigned for the delivery")
    order_type = fields.Char(string="Order Type", help="Type of the order")
    asset_latitude = fields.Float(string="Asset Latitude", help="Latitude of the vehicle's current location")
    asset_longitude = fields.Float(string="Asset Longitude", help="Longitude of the vehicle's current location")
    customer_latitude = fields.Float(string="Customer Latitude", help="Latitude of the vehicle's customer location")
    customer_longitude = fields.Float(string="Customer Longitude",
                                      help="Longitude of the vehicle's customer location")
    jde_state = fields.Selection([
        ('jde_confirmed', 'JDE Confirmed'),
        ('customer_service', 'Customer Service'),
        ('credit_control', 'Credit Control Hold'),
        ('order_at_WH', 'Order At WH'),
        ('order_confirmed', 'Order Confirmed'),
        ('ready_to_ship', 'Ready To Ship'),
        ('invoice_printed', 'Invoice Printed'),
        ('shipped_complete', 'Shipped Complete'),
        ('order_complete', 'Order Complete'),
        ('cancel', 'Cancelled'),
    ], string="JDE State")
    is_wallet_created = fields.Boolean(string="IS Wallet Created")

    def _sanity_check(self, separate_pickings=True):
        # JDE may report a delivery where nothing was shipped: validating it from the
        # API must go through (the moves get cancelled) instead of raising
        # "You cannot validate a transfer if no quantities are reserved nor done".
        if not self.env.context.get('validate_from_api'):
            return super()._sanity_check(separate_pickings)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit')
        without_quantities = self.filtered(lambda p: p.move_ids and all(
            float_is_zero(move.quantity, precision_digits=precision_digits)
            for move in p.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))))
        return super(StockPicking, self - without_quantities)._sanity_check(separate_pickings)

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.state != 'draft' and picking.return_id and picking.grv_order_type == 'GS':
                picking._create_return_order_jde_api()
            if picking.state in ['done', 'cancel']:
                if picking.move_ids and not any(picking.move_ids.mapped('quantity')):
                    picking.jde_state = 'cancel'
        return res

    def _return_order(self):
        # return_order_pick comes from website_return_management, which depends on this module.
        self.ensure_one()
        return self.return_order_pick if 'return_order_pick' in self._fields else False

    def _create_return_order_jde_api(self, retry_count=2):
        company = self.company_id
        auth_token = company.get_jde_token()
        create_order_return_jde_url = company.create_order_return_JDE_url

        headers = {
            'Content-Type': 'application/json',
        }

        payload = self._prepare_jde_payload(auth_token)

        _logger.info("Return Order Payload: %s", payload)

        for attempt in range(retry_count):
            try:
                response = requests.post(create_order_return_jde_url, headers=headers, json=payload,
                                         timeout=JDE_REQUEST_TIMEOUT)
                integration_record = self.env['integration.log'].sudo().create({
                    'name': 'JDE Return Order Request',
                    'url': str(create_order_return_jde_url),
                    'headers': str(headers),
                    'payload': str(payload),
                })
                if response.status_code == 200:
                    integration_record.write({'response': str(response.json())})
                    self.env.cr.commit()
                    dict_val = response.json()
                    self.write({'carrier_tracking_ref': dict_val.get('OrderNumber')})
                elif response.status_code == 502:
                    integration_record.write({'response': str(response.text)})
                    self.env.cr.commit()
                else:
                    integration_record.write({'response': str(response.json())})
                    self.env.cr.commit()
                _logger.info("Return Order Created in JDE Successfully: %s", response.text)

                self._logout_token(auth_token, company)
                return True

            except requests.exceptions.RequestException as e:
                _logger.error("Error Creating Return Order in JDE (Attempt %d): %s", attempt + 1, e)
                if attempt < retry_count - 1:
                    time.sleep(5)

        raise UserError(self.env._("Failed to create Return Order in JDE after %s attempts", retry_count))

    def _prepare_jde_payload(self, auth_token):
        grid_data = []
        for line in self.move_line_ids:
            item_number = (line.lot_id.name if self.company_id.is_ksa and line.lot_id
                           else line.product_id.product_tmpl_id.jde_product_id)
            grid_data.append({
                "ItemNumber": item_number,
                "QuantityOrdered": line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id),
                "UOM": line.product_id.uom_id.name,
                "UnitPrice": line.move_id.sale_line_id.jde_price_unit,
            })

        return_order = self._return_order()
        address_number_cus_id = self.partner_id.b2b_customer_id
        if return_order and return_order.sale_order and return_order.sale_order.partner_invoice_id:
            address_number_cus_id = return_order.sale_order.partner_invoice_id.b2b_customer_id

        return {
            "token": auth_token,
            "OrderCompany": "00101" if self.company_id.is_jordan else '00176',
            "BusinessUnit": "5201" if self.company_id.is_jordan else 'UAEFS',
            "AddressNumber": address_number_cus_id,
            "ShipTo": self.partner_id.b2b_customer_id,
            "CustomerPO": self.return_id.origin,
            "ReasonCode": return_order.code if return_order and return_order.code else "103",
            "JD048_Version": "JD003" if self.company_id.is_jordan else "TMB2B",
            "GridData": grid_data
        }

    def _logout_token(self, auth_token, company):
        headers = {
            'Content-Type': 'application/json',
        }
        logout_url = company.jde_logout_url
        payload_logout = {"token": auth_token}
        requests.post(logout_url, headers=headers, json=payload_logout, timeout=JDE_REQUEST_TIMEOUT)
        return

    def _credit_ewallet(self, partner, company, amount, picking):
        """ Credit a customer's eWallet with a returned amount and email the customer. """
        program = self.env['loyalty.program'].sudo().search(
            [('company_id', '=', company.id), ('program_type', '=', 'ewallet')], limit=1)
        if not program:
            return
        wallet_rec = self.env['loyalty.card'].sudo().search(
            [('partner_id', '=', partner.id), ('program_id', '=', program.id)])
        if not wallet_rec:
            wallet_rec = self.env['loyalty.card'].sudo().create({
                'program_id': program.id, 'points': amount, 'expiration_date': False, 'partner_id': partner.id
            })
        else:
            wallet_rec.write({'points': wallet_rec.points + amount})
        if wallet_rec:
            picking.sudo().write({'is_wallet_created': True})
        default_template = wallet_rec._get_default_template()
        self.env['mail.compose.message'].with_context(
            force_email=True,
        ).create({
            'res_ids': wallet_rec.ids,
            'template_id': default_template and default_template.id,
            'model': 'loyalty.card',
            'composition_mode': 'comment',
            'email_layout_xmlid': 'mail.mail_notification_light'
        }).action_send_mail()

    def _fetch_return_order_grv_from_jde(self):
        for company in self.env['res.company'].sudo().search([]):
            if company.create_order_return_odoo_scheduler and company.dta_schemaname:
                try:
                    auth_token = company.get_jde_token()
                    search_by_reference_url = company.create_order_return_odoo_scheduler
                    dta_schemaname = company.dta_schemaname

                    payload = {
                        "token": auth_token,
                        "DTA_SchemaName": dta_schemaname or "CRPDTA",
                        "LASTINTEGRATIONTIMESTAMP": datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                    }
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    response = requests.post(search_by_reference_url, headers=headers, json=payload,
                                             timeout=JDE_REQUEST_TIMEOUT)
                    integration_record = self.env['integration.log'].sudo().create({
                        'name': 'JDE Fetch Return Order',
                        'url': str(search_by_reference_url),
                        'headers': str(headers),
                        'payload': str(payload),
                    })
                    if response.status_code == 200:
                        integration_record.write({'response': str(response.json())})
                        pick_rows = response.json()
                    elif response.status_code == 502:
                        integration_record.write({'response': str(response.text)})
                        pick_rows = []
                    else:
                        integration_record.write({'response': str(response.json())})
                        pick_rows = response.json()
                    self.env.cr.commit()

                    updates = []
                    mapping_updates = {}
                    order = self.env['sale.order']
                    if 'rows' in pick_rows:
                        for row in pick_rows.get('rows'):
                            if row.get('GRV_TYPE') == 'SR':
                                sl_no_comp = int(row.get('LINENO'))
                                order = self.env['sale.order'].sudo().search([('name', '=', row.get('LPO').strip())],
                                                                             limit=1)
                                done_pick = order.picking_ids.filtered(
                                    lambda x: x.carrier_tracking_ref
                                    and x.carrier_tracking_ref == row.get('GRV_NUMBER').strip()
                                    and x.state in ['done'])
                                if order and not done_pick:
                                    picking = order.picking_ids.filtered(
                                        lambda x: x.carrier_tracking_ref
                                        and x.carrier_tracking_ref == row.get('ORIGINAL_ORDER').strip())

                                    return_pick = order.picking_ids.filtered(
                                        lambda x: x.carrier_tracking_ref
                                        and x.carrier_tracking_ref == row.get('GRV_NUMBER').strip())

                                    if picking and picking.state == 'done' and not return_pick:
                                        return_wizard = self.env['stock.return.picking'].sudo().create({
                                            'picking_id': picking.id,
                                        })

                                        product = self.env['product.product'].sudo().search(
                                            [('jde_product_id', '=', row.get('ITEM').strip())])
                                        return_move_unlink = return_wizard.product_return_moves.filtered(
                                            lambda x: x.product_id.id != product.id
                                            or sl_no_comp not in x.move_id.move_line_ids.mapped('sl_no_comp'))
                                        return_move_match = return_wizard.product_return_moves.filtered(
                                            lambda x: x.product_id.id == product.id
                                            and sl_no_comp in x.move_id.move_line_ids.mapped('sl_no_comp'))
                                        if return_move_unlink:
                                            return_move_unlink.unlink()

                                        if return_move_match:
                                            return_move_match.write({'quantity': abs(float(row.get('QUANTITY').strip()))})

                                        if return_wizard.product_return_moves:
                                            new_picking_obj = return_wizard._create_return()
                                            new_picking_id = new_picking_obj.id
                                            updates.append(new_picking_id)
                                            mapping_updates[new_picking_id] = (abs(float(row.get('ITEM_TOTAL')))
                                                                               if 'ITEM_TOTAL' in row else 0.0)
                                            new_picking_obj.write({
                                                'partner_id': picking.partner_id.id,
                                                'grv_order_type': row.get('GRV_TYPE'),
                                                'carrier_tracking_ref': row.get('GRV_NUMBER'),
                                            })
                                    if picking and return_pick:
                                        product = self.env['product.product'].sudo().search(
                                            [('jde_product_id', '=', row.get('ITEM').strip())])
                                        already_available = return_pick.move_ids.filtered(
                                            lambda x: x.product_id.id == product.id
                                            and sl_no_comp in x.origin_returned_move_id.move_line_ids.mapped('sl_no_comp'))
                                        if product and not already_available:
                                            for move in picking.move_ids.filtered(
                                                    lambda x: x.product_id.id == product.id
                                                    and sl_no_comp in x.move_line_ids.mapped('sl_no_comp')):
                                                if move.state == 'cancel':
                                                    continue
                                                if move.location_dest_usage == 'inventory':
                                                    continue  # scrapped

                                                vals = {
                                                    'product_id': product.id,
                                                    'product_uom_qty': abs(float(row.get('QUANTITY').strip())),
                                                    'product_uom': product.uom_id.id,
                                                    'picking_id': return_pick.id,
                                                    'state': 'draft',
                                                    'date': fields.Datetime.now(),
                                                    'location_id': move.location_dest_id.id,
                                                    'location_dest_id': return_pick.location_id.id or move.location_id.id,
                                                    'picking_type_id': return_pick.picking_type_id.id,
                                                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                                                    'origin_returned_move_id': move.id,
                                                    'procure_method': 'make_to_stock',
                                                }
                                                r = move.copy(vals)

                                                move_orig_to_link = move.move_dest_ids.mapped('returned_move_ids')
                                                move_orig_to_link |= move
                                                move_orig_to_link |= move \
                                                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel')) \
                                                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                                                move_dest_to_link = move.move_orig_ids.mapped('returned_move_ids')
                                                move_dest_to_link |= move.move_orig_ids.mapped('returned_move_ids') \
                                                    .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel')) \
                                                    .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                                                r.write({
                                                    'move_orig_ids': [Command.link(m.id) for m in move_orig_to_link],
                                                    'move_dest_ids': [Command.link(m.id) for m in move_dest_to_link],
                                                })

                                                updates.append(return_pick.id)
                                                mapping_updates[return_pick.id] = (abs(float(row.get('ITEM_TOTAL')))
                                                                                   if 'ITEM_TOTAL' in row else 0.0)
                            elif row.get('GRV_TYPE') == 'GS':
                                order = self.env['sale.order'].sudo().search([('name', '=', row.get('LPO').strip())],
                                                                             limit=1)
                                done_pick = order.picking_ids.filtered(
                                    lambda x: x.carrier_tracking_ref
                                    and x.carrier_tracking_ref == row.get('GRV_NUMBER').strip()
                                    and x.state in ['done'])
                                if done_pick and order.payment_term_id and order.payment_term_id.is_cash_payment_term:
                                    done_pick = done_pick[0]
                                    if not done_pick.is_wallet_created:
                                        partner = order.partner_id.parent_id or order.partner_id
                                        self._credit_ewallet(partner, done_pick.company_id,
                                                             abs(float(row.get('ITEM_TOTAL'))), done_pick)

                    return_pickings = self.env['stock.picking'].sudo().browse(set(updates))
                    _logger.info("Mapping Pickings %s", mapping_updates)
                    for pick in return_pickings:
                        pick.button_validate()
                        if pick.id in mapping_updates and not pick.is_wallet_created:
                            so_order = pick.move_ids.mapped('sale_line_id').mapped('order_id')
                            if (so_order and so_order.partner_id and so_order.payment_term_id
                                    and so_order.payment_term_id.is_cash_payment_term):
                                partner = so_order.partner_id.parent_id or so_order.partner_id
                                self._credit_ewallet(partner, pick.company_id,
                                                     abs(float(mapping_updates[pick.id])), pick)

                    _logger.info("JDE %d Return Order Created.", len(set(updates)))

                except requests.exceptions.RequestException as e:
                    _logger.error("Error updating JDE Delivery Note: %s", e)
