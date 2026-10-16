# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeaveReportCalendar(models.Model):
    _inherit = "hr.leave.report.calendar"

    # Standard restricts this field to Time Off Officers, which prevents regular
    # users from knowing why a colleague is absent. The private description
    # remains restricted.
    holiday_status_id = fields.Many2one(groups="base.group_user")

    @api.depends("employee_id.name", "holiday_status_id", "leave_id")
    def _compute_name(self):
        for leave in self:
            name = leave.employee_id.name or ""
            if leave.holiday_status_id:
                name += f" {leave.holiday_status_id.name}"
            leave.name = f"{name}: {leave.sudo().leave_id.duration_display}"
