# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.hr_holidays.tests.common import TestHrHolidaysCommon


class TestResourceCalendarGetDays(TestHrHolidaysCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Time Off with no validation for approval",
                "time_type": "leave",
                "requires_allocation": "yes",
                "allocation_validation_type": "no",
            }
        )

        cls.employee_emp.resource_calendar_id = cls.env.ref(
            "resource_calendar_get_days.resource_calendar_std_42h"
        ).id

    def test_resource_calendar_get_days_effect_allocation(self):
        emp_allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Bank Holiday",
                "holiday_type": "employee",
                "employee_ids": [(4, self.employee_emp.id)],
                "employee_id": self.employee_emp.id,
                "date_from": "2024-06-17",
                "holiday_status_id": self.leave_type.id,
                "number_of_days": 3,
                "allocation_type": "regular",
            }
        )
        emp_allocation.action_validate()
        # 3 days * 8.4 hour/day ~ 25.2
        self.assertEqual(round(emp_allocation.number_of_hours_display, 2), 25.2)
