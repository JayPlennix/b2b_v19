from odoo import fields, models


class ResConfigSettingsJDE(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_create_url = fields.Char("JDE Create Saleorder Url", readonly=False,
                                        related="company_id.sale_order_create_url")
    sale_order_status_url = fields.Char("JDE Saleorder Status Url", readonly=False,
                                        related="company_id.sale_order_status_url")
    search_by_reference_url = fields.Char("JDE Search By Reference Url", readonly=False,
                                          related="company_id.search_by_reference_url")
    create_order_return_JDE_url = fields.Char("JDE Order Return Create Url", readonly=False,
                                              related="company_id.create_order_return_JDE_url")
    create_order_return_odoo_scheduler = fields.Char("JDE Order Return Odoo Scheduler Url", readonly=False,
                                                     related="company_id.create_order_return_odoo_scheduler")
    sale_order_tracking_url = fields.Char("Sale Order Tracking Url", readonly=False,
                                          related="company_id.sale_order_tracking_url")
    sale_order_tracking_username = fields.Char("Sale Order Tracking Username", readonly=False,
                                               related="company_id.sale_order_tracking_username")
    sale_order_tracking_password = fields.Char("Sale Order Tracking Password", readonly=False,
                                               related="company_id.sale_order_tracking_password")
    sale_order_jde_invoiced_url = fields.Char("JDE Total Invoiced Url", readonly=False,
                                              related="company_id.sale_order_jde_invoiced_url")
    dta_schemaname = fields.Char("DTA_SchemaName", readonly=False, related="company_id.dta_schemaname")
    delivery_scheduler_url = fields.Char("Delivery Scheduler Url", readonly=False,
                                         related="company_id.delivery_scheduler_url")
    jde_last_status_integration_timestamp = fields.Datetime(
        "Last JDE Status Integration Timestamp", readonly=False,
        related="company_id.jde_last_status_integration_timestamp")
    jde_last_invoiced_integration_timestamp = fields.Datetime(
        "Last JDE Invoice Integration Timestamp", readonly=False,
        related="company_id.jde_last_invoiced_integration_timestamp")
