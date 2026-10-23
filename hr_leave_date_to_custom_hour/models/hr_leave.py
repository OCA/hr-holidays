# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HRLeave(models.Model):
    _inherit = "hr.leave"

    custom_hours_request_date_to = fields.Date(
        string="Request End Date for custom hours",
    )

    @api.depends(
        "custom_hours_request_date_to",
    )
    def _compute_date_from_to(self):
        res = super()._compute_date_from_to()
        for holiday in self:
            if holiday.request_unit_hours and holiday.custom_hours_request_date_to:
                holiday.date_to = holiday._to_utc(
                    holiday.custom_hours_request_date_to,
                    holiday.request_hour_to,
                    holiday.employee_id or holiday,
                )
        return res
