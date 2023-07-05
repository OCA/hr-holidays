from odoo import fields, models


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    code = fields.Char()

    def name_get(self):
        if self.requested_name_get():
            return super().name_get()

        return [
            (record.id, f"{record.code} - {record.name}")
            if record.code
            else (record.id, f"{record.name}")
            for record in self
        ]

    _sql_constraints = [
        (
            "code_uniq",
            "UNIQUE(code, company_id)",
            "The code must be unique per company!",
        )
    ]
