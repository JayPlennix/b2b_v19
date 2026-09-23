import base64
import io
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductUpdateWizard(models.TransientModel):
    _name = 'product.update.wizard'
    _description = 'Product Update Wizard'

    file = fields.Binary(string='Upload File', required=True)
    file_name = fields.Char(string='File Name')

    def action_update_products(self):
        """ Update the customer-facing name of products from an Excel file with the
        columns 'jde_product_id' and 'New Description'. """
        self.ensure_one()
        import openpyxl  # noqa: PLC0415
        if not self.file:
            raise UserError(_("Please upload an Excel file."))
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(base64.b64decode(self.file)), data_only=True)
        except Exception as error:
            raise UserError(_("Error reading file: %s", error)) from error

        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        if 'jde_product_id' not in headers or 'New Description' not in headers:
            raise UserError(_("Excel file must contain 'jde_product_id' and 'New Description' columns."))
        jde_idx = headers.index('jde_product_id')
        desc_idx = headers.index('New Description')

        products = self.env['product.template']
        missing = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            jde_id, new_desc = row[jde_idx], row[desc_idx]
            if not jde_id:
                continue
            product = products.search([('jde_product_id', '=', str(jde_id))], limit=1)
            if product:
                product.actual_name = new_desc
                products |= product
            else:
                missing.append(str(jde_id))
        if missing:
            _logger.info("Product update: no product for JDE ids %s", ', '.join(missing))
        message = _("%s product(s) updated.", len(products))
        if missing:
            message += _(" %s JDE item number(s) were not found: %s", len(missing), ', '.join(missing[:20]))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Products updated") if products else _("Nothing updated"),
                'message': message,
                'type': 'success' if products else 'warning',
                'sticky': bool(missing),
            },
        }
