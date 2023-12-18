# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class HolidaysLeave(models.Model):
    """Allocation Requests Access specifications: similar to leave requests"""

    _inherit = "hr.leave"

    def activity_update(self):
        """Updates activity for all leave_manager_ids"""
        if not self.employee_id.leave_manager_ids:
            super().activity_update()
        else:
            for manager in self.employee_id.leave_manager_ids:
                self.employee_id.sudo().leave_manager_id = manager
                super().activity_update()
                self.employee_id.sudo().leave_manager_id = False

    def _check_approval_update(self, state):
        """Checks that the leave manager is in leave_manager_ids"""
        if not self.employee_id.leave_manager_ids:
            super()._check_approval_update(state)
        else:
            for manager in self.employee_id.leave_manager_ids:
                if manager == self.env.user:
                    self.employee_id.sudo().leave_manager_id = manager.id
                    super()._check_approval_update(state)
                    self.employee_id.sudo().leave_manager_id = False
