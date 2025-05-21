# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# Copyright 2024- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from pytz import timezone, utc

import odoo.tests.common as common
from odoo.exceptions import UserError, ValidationError


class TestHolidaysLeaveRepeated(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.client_tz = timezone(cls.env.user.tz or "UTC")
        cls.date_start = datetime(2016, 12, 5, 8, 0, 0, 0)
        cls.date_end = datetime(2016, 12, 5, 18, 0, 0, 0)

        cls.calendar = cls.env["resource.calendar"].create({"name": "Calendar 1"})

        # Remove default attendances
        cls.calendar.attendance_ids.unlink()
        # Create full day attendance for every week day
        for i in range(0, 7):
            cls.env["resource.calendar.attendance"].create(
                {
                    "name": "Day " + str(i),
                    "dayofweek": str(i),
                    "hour_from": 8.0,
                    "hour_to": 18.0,
                    "calendar_id": cls.calendar.id,
                }
            )

        cls.employee_1 = cls.env["hr.employee"].create(
            {"name": "Employee 1", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {"name": "Employee 2", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_3 = cls.env["hr.employee"].create(
            {"name": "Employee 3", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_4 = cls.env["hr.employee"].create(
            {"name": "Employee 4", "resource_calendar_id": cls.calendar.id}
        )
        cls.employee_5 = cls.env["hr.employee"].create(
            {"name": "Failing Employee", "resource_calendar_id": cls.calendar.id}
        )

        cls.status_1 = cls.env["hr.leave.type"].create(
            {"name": "Repeating Status", "repeat": True}
        )

        allocation = cls.env["hr.leave.allocation"].create(
            {
                "name": "Initial Allocation",
                "holiday_status_id": cls.status_1.id,
                "number_of_days": 20,
                "employee_id": cls.employee_1.id,
                "date_from": date(2016, 1, 1),
            }
        )
        allocation.action_validate()
        allocation = cls.env["hr.leave.allocation"].create(
            {
                "name": "Initial Allocation",
                "holiday_status_id": cls.status_1.id,
                "number_of_days": 20,
                "employee_id": cls.employee_2.id,
                "date_from": date(2016, 1, 1),
            }
        )
        allocation.action_validate()
        allocation = cls.env["hr.leave.allocation"].create(
            {
                "name": "Initial Allocation",
                "holiday_status_id": cls.status_1.id,
                "number_of_days": 20,
                "employee_id": cls.employee_3.id,
                "date_from": date(2016, 1, 1),
            }
        )
        allocation.action_validate()
        allocation = cls.env["hr.leave.allocation"].create(
            {
                "name": "Initial Allocation",
                "holiday_status_id": cls.status_1.id,
                "number_of_days": 20,
                "employee_id": cls.employee_4.id,
                "date_from": date(2016, 1, 1),
            }
        )
        allocation.action_validate()

        cls.leave_1_list = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "repeat_every": "workday",
                "repeat_mode": "times",
                "repeat_limit": 5,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_1.id,
            }
        )
        cls.leave_2_list = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "repeat_every": "week",
                "repeat_mode": "times",
                "repeat_limit": 4,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_2.id,
            }
        )
        cls.leave_3_list = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "repeat_every": "biweek",
                "repeat_mode": "times",
                "repeat_limit": 3,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_3.id,
            }
        )
        cls.leave_4_list = cls.env["hr.leave"].create(
            {
                "holiday_status_id": cls.status_1.id,
                "repeat_every": "month",
                "repeat_mode": "times",
                "repeat_limit": 2,
                "request_date_from": cls.date_start,
                "request_date_to": cls.date_end,
                "employee_id": cls.employee_4.id,
            }
        )

    def test_01_count_repetitions(self):
        self.assertEqual(len(self.leave_1_list), 5)
        self.assertEqual(len(self.leave_2_list), 4)
        self.assertEqual(len(self.leave_3_list), 3)
        self.assertEqual(len(self.leave_4_list), 2)

    def test_02_workdays(self):
        for i in range(0, 5):
            check_from = self.client_tz.localize(self.date_start).astimezone(
                utc
            ) + timedelta(days=i)
            check_to = self.client_tz.localize(self.date_end).astimezone(
                utc
            ) + timedelta(days=i)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_1.id),
                    ("date_from", "=", check_from),
                    ("date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_03_weeks(self):
        for i in range(0, 4):
            check_from = self.client_tz.localize(self.date_start).astimezone(
                utc
            ) + timedelta(days=i * 7)
            check_to = self.client_tz.localize(self.date_end).astimezone(
                utc
            ) + timedelta(days=i * 7)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_2.id),
                    ("date_from", "=", check_from),
                    ("date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_04_biweeks(self):
        for i in range(0, 3):
            check_from = self.client_tz.localize(self.date_start).astimezone(
                utc
            ) + timedelta(days=i * 14)
            check_to = self.client_tz.localize(self.date_end).astimezone(
                utc
            ) + timedelta(days=i * 14)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_3.id),
                    ("date_from", "=", check_from),
                    ("date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_05_months(self):
        for i in range(0, 2):
            check_from = self.client_tz.localize(self.date_start).astimezone(
                utc
            ) + timedelta(days=i * 28)
            check_to = self.client_tz.localize(self.date_end).astimezone(
                utc
            ) + timedelta(days=i * 28)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_4.id),
                    ("date_from", "=", check_from),
                    ("date_to", "=", check_to),
                ]
            )
            self.assertEqual(len(leaves), 1)

    def test_06_check_dates(self):
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "repeat_every": "workday",
                    "repeat_limit": -1,
                    "request_date_from": self.date_start,
                    "request_date_to": self.date_end,
                    "employee_id": self.employee_5.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "repeat_every": "workday",
                    "repeat_mode": "date",
                    "repeat_end_date": self.date_start - timedelta(days=1),
                    "request_date_from": self.date_start,
                    "request_date_to": self.date_end,
                    "employee_id": self.employee_5.id,
                }
            )

    def test_07_check_dates(self):
        date_start = datetime(2019, 2, 18, 8, 0, 0, 0)
        date_end = datetime(2019, 2, 20, 18, 0, 0, 0)
        with self.assertRaises(UserError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.status_1.id,
                    "repeat_every": "workday",
                    "repeat_mode": "times",
                    "repeat_limit": 5,
                    "request_date_from": date_start,
                    "request_date_to": date_end,
                    "employee_id": self.employee_5.id,
                }
            )

    def test_08_workdays_with_weekend(self):
        date_start = datetime(2019, 3, 1, 8, 0, 0, 0)
        date_end = datetime(2019, 3, 1, 18, 0, 0, 0)
        self.env["hr.leave"].create(
            {
                "holiday_status_id": self.status_1.id,
                "repeat_every": "workday",
                "repeat_mode": "times",
                "repeat_limit": 5,
                "request_date_from": date_start,
                "request_date_to": date_end,
                "employee_id": self.employee_1.id,
            }
        )
        for i in range(0, 7):
            datetime_from = self.client_tz.localize(self.date_start).astimezone(
                utc
            ) + timedelta(days=i)
            datetime_to = self.client_tz.localize(self.date_end).astimezone(
                utc
            ) + timedelta(days=i)
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", self.status_1.id),
                    ("employee_id", "=", self.employee_1.id),
                    ("date_from", "=", datetime_from),
                    ("date_to", "=", datetime_to),
                ]
            )
            if datetime_from.weekday() < 5:  # is a weekday
                self.assertEqual(len(leaves), 1)
            else:  # is weekend
                self.assertEqual(len(leaves), 0)

    def test_09_check_repeat_end_date(self):
        old_date = date(2025, 3, 18)
        date_start = datetime(2025, 2, 18, 8, 0, 0, 0)
        date_end = datetime(2025, 2, 18, 18, 0, 0, 0)
        allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Initial Allocation",
                "holiday_status_id": self.status_1.id,
                "number_of_days": 20,
                "employee_id": self.employee_5.id,
                "date_from": date(2025, 1, 1),
            }
        )
        allocation.action_validate()
        leaves = self.env["hr.leave"].create(
            {
                "holiday_status_id": self.status_1.id,
                "repeat_every": "week",
                "repeat_mode": "date",
                "repeat_end_date": old_date,
                "request_date_from": date_start,
                "request_date_to": date_end,
                "employee_id": self.employee_5.id,
            }
        )
        self.assertEqual(len(leaves), 5)
