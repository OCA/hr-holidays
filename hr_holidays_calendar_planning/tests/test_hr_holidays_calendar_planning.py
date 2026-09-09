# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.hr_employee_calendar_planning.tests.test_hr_employee_calendar_planning import (  # noqa: E501
    TestHrEmployeeCalendarPlanningCommon,
)


class TestHrHolidaysEmployeeCalendarPlanning(TestHrEmployeeCalendarPlanningCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_tye = cls.env["hr.leave.type"].create(
            {
                "name": "Test type A",
                "requires_allocation": "no",
                "request_unit": "hour",
            }
        )
        cls.employee.tz = "UTC"

    @mute_logger("odoo.models.unlink")
    def test_hr_leave_misc_flexible_hours_request_unit_half(self):
        self.calendar1.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 40,
                "stored_hours_per_day": 8,
            }
        )
        self.calendar2.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 20,
                "stored_hours_per_day": 4,
            }
        )
        self.employee.calendar_ids = [Command.clear()] + [
            Command.create(
                {
                    "date_start": "2025-01-01",
                    "date_end": "2025-12-31",
                    "calendar_id": self.calendar1.id,
                },
            ),
            Command.create(
                {"date_start": "2026-01-01", "calendar_id": self.calendar2.id}
            ),
        ]
        leave_2025 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2025-01-01",
                default_request_date_to="2025-01-01",
                default_request_unit_half=True,
            )
        )
        self.assertEqual(leave_2025.number_of_hours, 4.0)
        self.assertEqual(leave_2025.date_from.hour, 8)
        self.assertEqual(leave_2025.date_to.hour, 12)
        leave_2026 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2026-01-01",
                default_request_date_to="2026-01-01",
                default_request_unit_half=True,
            )
        )
        self.assertEqual(leave_2026.number_of_hours, 2.0)
        self.assertEqual(leave_2026.date_from.hour, 10)
        self.assertEqual(leave_2026.date_to.hour, 12)
        leave_2024 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2024-12-30",
                default_request_date_to="2024-12-30",
                default_request_unit_half=True,
            )
        )
        self.assertEqual(leave_2024.number_of_hours, 0)
        self.assertEqual(leave_2024.date_from.hour, 0)
        self.assertEqual(leave_2024.date_to.hour, 0)

    @mute_logger("odoo.models.unlink")
    def test_hr_leave_misc_flexible_hours_full_day(self):
        self.calendar1.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 40,
                "stored_hours_per_day": 8,
            }
        )
        self.calendar2.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 20,
                "stored_hours_per_day": 4,
            }
        )
        self.employee.calendar_ids = [Command.clear()] + [
            Command.create(
                {
                    "date_start": "2025-01-01",
                    "date_end": "2025-12-31",
                    "calendar_id": self.calendar1.id,
                },
            ),
            Command.create(
                {"date_start": "2026-01-01", "calendar_id": self.calendar2.id}
            ),
        ]
        leave_2025 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2025-01-01",
                default_request_date_to="2025-01-01",
            )
        )
        self.assertEqual(leave_2025.number_of_hours, 8.0)
        self.assertEqual(leave_2025.date_from.hour, 8)
        self.assertEqual(leave_2025.date_to.hour, 16)
        leave_2026 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2026-01-01",
                default_request_date_to="2026-01-01",
            )
        )
        self.assertEqual(leave_2026.number_of_hours, 4.0)
        self.assertEqual(leave_2026.date_from.hour, 10)
        self.assertEqual(leave_2026.date_to.hour, 14)
        leave_2024 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2024-12-30",
                default_request_date_to="2024-12-30",
            )
        )
        self.assertEqual(leave_2024.number_of_hours, 0)
        self.assertEqual(leave_2024.date_from.hour, 0)
        self.assertEqual(leave_2024.date_to.hour, 0)

    @mute_logger("odoo.models.unlink")
    def test_hr_leave__flexible_hours_request_unit_hours(self):
        self.calendar1.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 40,
                "stored_hours_per_day": 8,
            }
        )
        self.calendar2.write(
            {
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 20,
                "stored_hours_per_day": 4,
            }
        )
        self.employee.calendar_ids = [Command.clear()] + [
            Command.create(
                {
                    "date_start": "2025-01-01",
                    "date_end": "2025-12-31",
                    "calendar_id": self.calendar1.id,
                },
            ),
            Command.create(
                {"date_start": "2026-01-01", "calendar_id": self.calendar2.id}
            ),
        ]
        leave_2025 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2025-01-01",
                default_request_date_to="2025-01-01",
                default_request_unit_hours=True,
                default_request_hour_from=11,
                default_request_hour_to=12,
            )
        )
        self.assertEqual(leave_2025.number_of_hours, 1.0)
        leave_2026 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2026-01-01",
                default_request_date_to="2026-01-01",
                default_request_unit_hours=True,
                default_request_hour_from=8,
                default_request_hour_to=9,
            )
        )
        self.assertEqual(leave_2026.number_of_hours, 1.0)
        leave_2024 = Form(
            self.env["hr.leave"].with_context(
                default_employee_id=self.employee.id,
                default_holiday_status_id=self.leave_tye.id,
                default_request_date_from="2024-12-30",
                default_request_date_to="2024-12-30",
                default_request_unit_hours=True,
                default_request_hour_from=8,
                default_request_hour_to=9,
            )
        )
        self.assertEqual(leave_2024.number_of_hours, 0.0)
