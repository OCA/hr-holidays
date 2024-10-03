# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from freezegun import freeze_time

from odoo.addons.hr_holidays.tests.test_allocations import TestAllocations


class TestHrHolidaysRemainLeaves(TestAllocations):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_hr_holidays_remaining_leaves(self):
        emp_allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Bank Holiday",
                "holiday_type": "employee",
                "employee_ids": [(4, self.employee.id)],
                "employee_id": self.employee.id,
                "date_from": "2024-06-17",
                "holiday_status_id": self.leave_type.id,
                "number_of_days": 3,
                "allocation_type": "regular",
            }
        )
        emp_allocation.action_validate()
        with freeze_time("2024-06-19"):
            leave_current = self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee.id,
                    "date_from": "2024-06-19",
                    "date_to": "2024-06-19",
                }
            )
            leave_current.action_validate()
        with freeze_time("2024-06-25"):
            leave_fututre = self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee.id,
                    "date_from": "2024-06-25",
                    "date_to": "2024-06-25",
                }
            )
            leave_fututre.action_validate()

        with freeze_time("2024-06-23"):
            self.assertEqual(emp_allocation.remaining_leaves_days, 1.0)
            self.assertEqual(emp_allocation.remaining_leaves_hours, 8.0)
            self.assertEqual(emp_allocation.remaining_leaves_display, "1.0 days")
            self.assertEqual(emp_allocation.remaining_leaves_current_days, 2.0)
            self.assertEqual(emp_allocation.remaining_leaves_current_hours, 16.0)
            self.assertEqual(
                emp_allocation.remaining_leaves_current_display, "2.0 days"
            )
