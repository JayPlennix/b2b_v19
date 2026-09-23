# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartnerb2b(models.Model):
    _inherit = "res.partner"

    b2b_customer_id = fields.Integer("B2B_customer_id")
    create_via_api = fields.Boolean("create_via_api")
    customer_group = fields.Char("Customer Group")
    customer_group_name = fields.Char("Customer Group name")
    customer_channel = fields.Char("Customer Channel")
    customer_channel_name = fields.Char("Customer Channel Name")
    customer_area = fields.Char("Customer Area")
    customer_area_name = fields.Char("Customer Areaname")
    customer_subarea = fields.Char("Customer Subarea")
    customer_subarea_name = fields.Char("Customer Subareaname")
    timestamp_jde = fields.Datetime("Timestamp JDE")
    customer_type = fields.Char("Customer Type")
    customer_mailing_name = fields.Char("Customer Mailingname")
    create_b2b_owner = fields.Char("Customer Create Owner")

    def write(self, vals):
        # Changing a partner's company must not be pushed down to its contacts and
        # addresses: each JDE child keeps the company it was created with.
        # Core res.partner.write() cascades with child_ids.write({'company_id': ...});
        # that nested call is recognised by the context key and skipped.
        if self.env.context.get('b2b_skip_child_company_cascade') and set(vals) == {'company_id'}:
            return True
        if 'company_id' in vals:
            return super(ResPartnerb2b, self.with_context(b2b_skip_child_company_cascade=True)).write(vals)
        return super().write(vals)
