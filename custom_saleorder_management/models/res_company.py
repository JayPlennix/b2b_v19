from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Also defined in custom_website, which depends on this module; defined here so
    # this module and the ones depending on it do not rely on custom_website.
    is_ksa = fields.Boolean(string='Is Transmed KSA')
    is_jordan = fields.Boolean(string='Is Transmed Jordan')

    sale_order_create_url = fields.Char("JDE Create Saleorder Url")
    sale_order_status_url = fields.Char("JDE Saleorder Status Url")
    search_by_reference_url = fields.Char("JDE Search By Reference Url")
    create_order_return_JDE_url = fields.Char("JDE Order Return Create Url")
    create_order_return_odoo_scheduler = fields.Char("JDE Order Return Odoo Scheduler Url")
    sale_order_tracking_url = fields.Char("Sale Order Tracking Url")
    sale_order_tracking_username = fields.Char("Sale Order Tracking Username")
    sale_order_tracking_password = fields.Char("Sale Order Tracking Password")
    sale_order_jde_invoiced_url = fields.Char("JDE Total Invoiced Url")
    dta_schemaname = fields.Char("DTA_SchemaName")
    delivery_scheduler_url = fields.Char("Delivery Scheduler Url")
    jde_last_status_integration_timestamp = fields.Datetime("Last JDE Status Integration Timestamp")
    jde_last_invoiced_integration_timestamp = fields.Datetime("Last JDE Invoice Integration Timestamp")
