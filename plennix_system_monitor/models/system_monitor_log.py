# -*- coding: utf-8 -*-
import base64
import csv
from datetime import datetime, time, timedelta
from io import StringIO

from odoo import api, fields, models


class SystemMonitorLog(models.Model):
    _name = "system.monitor.log"
    _inherit = ["mail.thread"]
    _description = "Plennix System Monitor"
    _rec_name = "exception"
    _order = "create_date desc"

    active = fields.Boolean(default=True)

    # Request Params
    method = fields.Char("Method")
    method_args = fields.Char("Method Arguments")
    model = fields.Char("Model")
    allowed_companies_ids = fields.Many2many(comodel_name="res.company")
    lang = fields.Char("Language")
    tz = fields.Char("Timezone")
    user_id = fields.Many2one(comodel_name="res.users")

    # Response Params
    stacktrace = fields.Text("Debug")
    exception = fields.Char("Exception")
    description = fields.Char("Description")

    # Raw
    request = fields.Text("Request")
    response = fields.Text("Response")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.handle_error()
        return res

    def send_daily_log(self):
        today_start = datetime.combine(fields.Date.context_today(self), time.min)
        errors_today = self.sudo().search([
            ("create_date", ">=", today_start),
            ("create_date", "<", today_start + timedelta(days=1)),
        ])
        if errors_today:
            errors_today.handle_error()

    @api.model
    def _get_logger_users(self):
        user_ids = self.env["ir.config_parameter"].sudo().get_param("logger_user_ids") or ""
        user_ids = [int(user_id) for user_id in user_ids.strip("[]").split(",") if user_id.strip()]
        return self.env["res.users"].sudo().browse(user_ids).exists()

    def handle_error(self):
        log_partners = self._get_logger_users().partner_id
        if not self or not log_partners:
            return  # nobody to notify

        # Create Attachment
        file = StringIO()
        dict_writer = csv.DictWriter(file, fieldnames=list(self[:1].sheet_mapper.keys()))
        dict_writer.writeheader()
        dict_writer.writerows(line.sheet_mapper for line in self)

        attachment = self.env["ir.attachment"].sudo().create({
            "name": f"Error Log {fields.Date.today()}.csv",
            "datas": base64.b64encode(file.getvalue().encode("utf-8")),
            "mimetype": "text/csv",
        })
        # Mail it to log users
        template = self.env.ref("plennix_system_monitor.email_template_daily_errors_log")
        template.sudo().send_mail(
            self[:1].id,
            email_values={
                "author_id": self.env.ref("base.partner_root").id,
                "recipient_ids": log_partners.ids,
                "attachment_ids": attachment.ids,
            },
            email_layout_xmlid="mail.mail_notification_light",
        )

    @property
    def sheet_mapper(self):
        return {
            "Timestamp": self.create_date,
            "Model": self.model,
            "Method": self.method,
            "Method Arguments": self.method_args,
            "User": self.user_id.name,
            "Allowed Companies": self.allowed_companies_ids.mapped("name"),
            "Timezone": self.tz,
            "Language": self.lang,
            "Debug": self.stacktrace,
        }
