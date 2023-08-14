# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from collections import defaultdict

from odoo import models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _update_overtime(self, employee_attendance_dates=None):
        """Set the flag in context to exclude public holidays"""
        if employee_attendance_dates is None:
            employee_attendance_dates = self._get_attendances_dates()
        # also set the flag on the employees' context as some code paths get dates from there
        employee_attendance_dates = defaultdict(
            employee_attendance_dates.default_factory,
            {
                employee.with_context(
                    exclude_public_holidays=True, employee_id=employee.id
                ): dates
                for employee, dates in employee_attendance_dates.items()
            },
        )
        return super(
            HrAttendance, self.with_context(exclude_public_holidays=True)
        )._update_overtime(employee_attendance_dates=employee_attendance_dates)
