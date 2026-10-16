# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _update_overtime(self, attendance_domain=None):
        """Set the flag in context to exclude public holidays"""
        return super(
            HrAttendance, self.with_context(exclude_public_holidays=True)
        )._update_overtime(attendance_domain=attendance_domain)
