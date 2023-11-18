# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo.addons.hr_holidays_public.tests.test_holidays_public import (
    TestHolidaysPublicBase,
)


class TestHrHolidaysPublicOvertime(TestHolidaysPublicBase):
    def setUp(self):
        super().setUp()
        self.employee.resource_calendar_id = self.env.ref(
            "resource.resource_calendar_std"
        )
        self.employee.company_id.write(
            {
                "overtime_start_date": "1994-10-13",
                "hr_attendance_overtime": True,
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
        overtime = self.env["hr.attendance.overtime"].search(
            [
                ("date", "=", "1994-10-14"),
                ("employee_id", "=", self.employee.id),
            ]
        )
        self.assertEqual(overtime.duration, 1)
        attendance.check_out = "1994-10-14 14:00:00"
        self.assertEqual(overtime.duration, 2)
