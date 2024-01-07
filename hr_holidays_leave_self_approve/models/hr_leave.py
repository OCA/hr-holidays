# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_approval_update(self, state):
        if self.env.is_admin():
            return
        if state in ("validate", "refuse"):
            current_employee = self.env.user.employee_id
            if current_employee.user_id == current_employee.leave_manager_id:
                # Filter out self-approved leaves
                self = self.filtered_domain(
                    [("employee_id", "!=", current_employee.id)]
                )
        super()._check_approval_update(state)
