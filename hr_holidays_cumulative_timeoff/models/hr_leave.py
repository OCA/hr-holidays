from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    cumulative_remaining_timeoff = fields.Float(
        compute="_compute_timeoffs",
        store=True,
    )
    cumulative_used_timeoff = fields.Float(
        compute="_compute_timeoffs",
        store=True,
    )

    def _get_plain_unit_value(self):
        self.ensure_one()
        if self.holiday_status_id.request_unit == "day":
            return self.number_of_days_display
        else:
            return self.number_of_hours_display

    @api.depends("state", "date_from", "date_to", "holiday_status_id.request_unit")
    def _compute_timeoffs(self):
        employees = self.mapped("employee_id")
        for employee in employees:
            leaves = self.filtered(lambda lv, emp=employee: lv.employee_id == emp)
            leave_types = leaves.mapped("holiday_status_id")
            for leave_type in leave_types:
                if leave_type.allocation_type == "no":
                    continue
                max_leave_time = leave_type.with_context(
                    employee_id=employee.id
                ).max_leaves
                relevant_leaves = self.search(
                    [
                        ("employee_id", "=", employee.id),
                        ("holiday_status_id", "=", leave_type.id),
                    ],
                    order="date_from asc",
                )
                time_used = 0
                for leave in relevant_leaves:
                    time_used += leave._get_plain_unit_value()
                    leave.cumulative_used_timeoff = time_used
                    leave.cumulative_remaining_timeoff = max_leave_time - time_used
