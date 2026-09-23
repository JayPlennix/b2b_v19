from odoo import Command, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    logger_user_ids = fields.Many2many(comodel_name="res.users", domain=[("share", "=", False)])

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param("logger_user_ids", str(self.logger_user_ids.ids))

    @api.model
    def get_values(self):
        values = super().get_values()
        values["logger_user_ids"] = [Command.set(self.env["system.monitor.log"]._get_logger_users().ids)]
        return values
