# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class HolidaysLeave(models.Model):
    """Allocation Requests Access specifications: similar to leave requests"""

    _inherit = "hr.leave"

    def activity_update(self):
        """Updates activity for all leave_manager_ids"""
        res = super().activity_update()
        for manager in self.employee_id.leave_manager_ids:
            old_manager = self.employee_id.leave_manager_id
            self.employee_id.leave_manager_id = manager
            super().activity_update()
            self.employee_id.leave_manager_id = old_manager
        return res

    def _check_approval_update(self, state):
        """Checks that the leave manager is in leave_manager_ids"""
        res = super()._check_approval_update(state)
        for manager in self.employee_id.leave_manager_ids:
            if manager == self.env.user:
                old_manager = self.employee_id.leave_manager_id
                self.employee_id.leave_manager_id = manager
                super()._check_approval_update(state)
                self.employee_id.leave_manager_id = old_manager
                break
        return res
