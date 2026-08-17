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
        return super()._compute_date_from_to()

    def _get_attendances(self, employee, request_date_from, request_date_to):
        if len(self) == 1 and self.request_unit_hours:
            self.request_date_to = request_date_to = (
                self.custom_hours_request_date_to or self.request_date_to
            )
        return super()._get_attendances(employee, request_date_from, request_date_to)
