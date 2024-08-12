from odoo import models


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    def _propagate_cumulative_timeoff_recompute(self):
        HrLeave = self.env["hr.leave"]
        to_propagate = HrLeave
        for hla in self:
            to_propagate += HrLeave.search(
                [
                    ("employee_id", "=", hla.employee_id.id),
                    ("holiday_status_id", "=", hla.holiday_status_id.id),
                ]
            )
        if to_propagate:
            to_propagate._compute_timeoffs()

    def action_approve(self):
        res = super().action_approve()

        valid_allocations = self.filtered(
            lambda hla: hla.holiday_status_id.leave_validation_type in ("hr", "manager")
        )
        if valid_allocations:
            valid_allocations._propagate_cumulative_timeoff_recompute()

        return res

    def action_validate(self):
        res = super().action_validate()

        valid_allocations = self.filtered(
            lambda hla: hla.holiday_status_id.leave_validation_type == "both"
        )
        if valid_allocations:
            valid_allocations._propagate_cumulative_timeoff_recompute()

        return res
