# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class HolidaysLeave(models.Model):
    """Allocation Requests Access specifications: similar to leave requests"""

    _inherit = "hr.leave"

    def _get_responsible_for_approval(self):
        self.ensure_one()

        responsible = self.env["res.users"]
        if self.validation_type == "manager" or (
            self.validation_type == "both" and self.state == "confirm"
        ):
            if self.employee_id.leave_manager_ids:
                responsible = self.employee_id.leave_manager_ids
            elif self.employee_id.leave_manager_id:
                responsible = self.employee_id.leave_manager_id
            elif self.employee_id.parent_id.user_id:
                responsible = self.employee_id.parent_id.user_id
        elif self.validation_type == "hr" or (
            self.validation_type == "both" and self.state == "validate1"
        ):
            if self.holiday_status_id.responsible_ids:
                responsible = self.holiday_status_id.responsible_ids
        return responsible
