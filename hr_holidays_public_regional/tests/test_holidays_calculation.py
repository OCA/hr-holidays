# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestRegionalHolidaysComputeDaysBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.HrLeave = cls.env["hr.leave"]
        cls.HrLeaveType = cls.env["hr.leave.type"]
        cls.HrHolidaysPublicRegional = cls.env["hr.holidays.public.regional"]
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Calendar", "attendance_ids": []}
        )
        for day in range(5):  # From monday to friday
            cls.calendar.attendance_ids = [
                (
                    0,
                    0,
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "08",
                        "hour_to": "12",
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "14",
                        "hour_to": "18",
                    },
                ),
            ]
        # Use a very old year for avoiding to collapse with current data
        cls.public_regional_holiday1 = cls.HrHolidaysPublicRegional.create(
            {
                "name": "Public Regional Holiday 1",
                "year": 1946,
                "line_ids": [(0, 0, {"name": "Christmas", "date": "1946-12-25"})],
            }
        )
        cls.public_regional_holiday2 = cls.HrHolidaysPublicRegional.create(
            {
                "name": "Public Regional Holiday 2",
                "year": 1946,
                "line_ids": [
                    (0, 0, {"name": "Before Christmas", "date": "1946-12-24"}),
                    (
                        0,
                        0,
                        {
                            "name": "Even More Before Christmas",
                            "date": "1946-12-23",
                        },
                    ),
                ],
            }
        )

        cls.public_holiday_global_1947 = cls.HrHolidaysPublicRegional.create(
            {
                "name": "Public Holiday Global 1947",
                "year": 1947,
                "line_ids": [
                    (0, 0, {"name": "New Eve", "date": "1947-01-01"}),
                    (0, 0, {"name": "New Eve extended", "date": "1947-01-02"}),
                ],
            }
        )

        cls.holiday_type = cls.HrLeaveType.create({"name": "Leave Type Test"})
        cls.holiday_type_no_excludes = cls.HrLeaveType.create(
            {
                "name": "Leave Type Test Without excludes",
                "exclude_public_holidays": False,
            }
        )

        cls.employee_1 = cls.env["hr.employee"].create(
            {
                "name": "Employee 1",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.env["hr.employee.regional.calendar"].create(
            {
                "employee_id": cls.employee_1.id,
                "calendar_id": cls.public_regional_holiday1.id,
                "start_date": "1946-01-01",
                "end_date": "1946-12-31",
            }
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {
                "name": "Employee 2",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.env["hr.employee.regional.calendar"].create(
            {
                "employee_id": cls.employee_2.id,
                "calendar_id": cls.public_regional_holiday2.id,
                "start_date": "1946-01-01",
                "end_date": "1946-12-31",
            }
        )


class TestHolidaysRegionalComputeDays(TestRegionalHolidaysComputeDaysBase):
    def test_number_days_excluding_employee_1(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_1.id,
            }
        )
        leave_request._compute_duration()
        self.assertEqual(leave_request.number_of_days, 4)

    def _test_number_days_excluding_employee_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        leave_request._compute_duration()
        self.assertEqual(leave_request.number_of_days, 2)

    def test_number_days_not_excluding(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type_no_excludes.id,
                "employee_id": self.employee_1.id,
            }
        )
        leave_request._compute_duration()
        self.assertEqual(leave_request.number_of_days, 5)

    def test_number_days_across_year(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1947-01-03 23:59:59",  # Friday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_1.id,
            }
        )
        leave_request._compute_duration()
        self.assertEqual(leave_request.number_of_days, 9)

    def test_number_days_across_year_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1947-01-03 23:59:59",  # Friday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        leave_request._compute_duration()
        self.assertEqual(leave_request.number_of_days, 8)

    def test_number_of_hours_excluding_employee_2(self):
        self.holiday_type.request_unit = "hour"
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )

        self.assertEqual(leave_request.number_of_days, 3)
        self.assertEqual(leave_request.number_of_hours_display, 24)
