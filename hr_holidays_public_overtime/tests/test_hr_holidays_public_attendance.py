# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo.addons.hr_holidays_public.tests.test_holidays_public import (
    TestHolidaysPublic,
)


class TestHrHolidaysPublicOvertime(TestHolidaysPublic):
    def setUp(self):
        super().setUp()
        self.employee.resource_calendar_id = self.env["resource.calendar"].create(
            {
                "name": "Test Calendar 40h",
                "full_time_required_hours": 40,
            }
        )
        self.employee.company_id.write(
            {
                "hr_attendance_display_overtime": True,
            }
        )

    def test_overtime_calculation(self):
        attendance = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": "1994-10-14 12:00:00",
                "check_out": "1994-10-14 13:00:00",
            }
        )
        domain = [("date", "=", "1994-10-14"), ("employee_id", "=", self.employee.id)]
        overtime = self.env["hr.attendance.overtime.line"].search(domain)
        self.assertEqual(overtime.duration, 1.0)
        attendance.check_out = "1994-10-14 14:00:00"
        updated_overtime = self.env["hr.attendance.overtime.line"].search(domain)
        self.assertEqual(updated_overtime.duration, 2.0)
