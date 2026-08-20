from odoo import api, fields, models


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    code = fields.Char()

    @api.depends_context("requested_name_get")
    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            if record.requested_name_get():
                convert = self._fields[self._rec_name].convert_to_display_name
                record.display_name = convert(record[self._rec_name], record)
            else:
                if record.code:
                    record.display_name = f"{record.code} - {record.name}"
                else:
                    record.display_name = record.name

    def requested_name_get(self):
        return self.env.context.get("requested_name_get")

    _code_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The code must be unique per company!",
    )
