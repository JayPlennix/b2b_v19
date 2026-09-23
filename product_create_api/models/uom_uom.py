from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    jde_package_name = fields.Char(
        string="JDE Package", index='btree_not_null',
        help="Name of the JDE package this packaging unit was created from.")
