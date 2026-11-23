# Copyright 2015 iDT LABS (http://www.@idtlabs.sl)
# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import new_test_user

from odoo.addons.calendar_public_holiday.tests.test_calendar_public_holiday import (
    TestCalendarPublicHoliday,
)


class TestHolidaysComputeDaysBase(TestCalendarPublicHoliday):
    _test_user_groups = (
        "base.group_user",
        "hr.group_hr_user",
        "hr_holidays.group_hr_holidays_manager",
        "base.group_system",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HrLeave = cls.env["hr.leave"]
        cls.HrLeaveType = cls.env["hr.work.entry.type"]
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Calendar", "attendance_ids": []}
        )
        for day in range(5):  # From monday to friday
            cls.calendar.attendance_ids = [
                Command.create(
                    {
                        "dayofweek": str(day),
                        "hour_from": 8,
                        "hour_to": 12,
                    },
                ),
                Command.create(
                    {
                        "dayofweek": str(day),
                        "hour_from": 14,
                        "hour_to": 18,
                    },
                ),
            ]
        cls.address_1 = cls.env["res.partner"].create(
            {"name": "Address 1", "country_id": cls.env.ref("base.uk").id}
        )
        cls.address_2 = cls.env["res.partner"].create(
            {
                "name": "Address 1",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_cr").id,
            }
        )
        cls.employee_1 = cls.env["hr.employee"].create(
            {
                "name": "Employee 1",
                "resource_calendar_id": cls.calendar.id,
                "address_id": cls.address_1.id,
            }
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {
                "name": "Employee 2",
                "resource_calendar_id": cls.calendar.id,
                "address_id": cls.address_2.id,
            }
        )
        cls.employee_user = new_test_user(
            cls.env,
            login="public_holiday_employee",
            groups="base.group_user",
            name="Employee 2",
        )
        cls.employee_2.user_id = cls.employee_user
        # Use a very old year for avoiding to collapse with current data
        cls.public_holiday_global = cls.holiday_model.create(
            {
                "year": 1946,
                "line_ids": [
                    Command.create({"name": "Christmas", "date": "1946-12-25"}),
                ],
            }
        )
        cls.public_holiday_country = cls.holiday_model.create(
            {
                "year": 1946,
                "country_id": cls.address_2.country_id.id,
                "line_ids": [
                    Command.create({"name": "Before Christmas", "date": "1946-12-24"}),
                    Command.create(
                        {
                            "name": "Even More Before Christmas",
                            "date": "1946-12-23",
                            "state_ids": [Command.set(cls.address_2.state_id.ids)],
                        },
                    ),
                ],
            }
        )

        cls.public_holiday_global_1947 = cls.holiday_model.create(
            {
                "year": 1947,
                "line_ids": [
                    Command.create({"name": "New Eve", "date": "1947-01-01"}),
                    Command.create({"name": "New Eve extended", "date": "1947-01-02"}),
                ],
            }
        )

        cls.holiday_type = cls.HrLeaveType.create(
            {
                "name": "Leave Type Test",
                "code": "LEAVE_TEST",
                "unit_of_measure": "day",
                "time_off_selectable": True,
                "exclude_public_holidays": True,
            }
        )
        cls.holiday_type_no_excludes = cls.HrLeaveType.create(
            {
                "name": "Leave Type Test Without excludes",
                "code": "LEAVE_TEST_NO_EX",
                "unit_of_measure": "day",
                "time_off_selectable": True,
                "exclude_public_holidays": False,
            }
        )


class TestHolidaysComputeDays(TestHolidaysComputeDaysBase):
    def test_number_days_excluding_employee_1(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_1.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 4)

    def _test_number_days_excluding_employee_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 2)

    def test_number_days_not_excluding(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "work_entry_type_id": self.holiday_type_no_excludes.id,
                "employee_id": self.employee_1.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 5)

    def test_number_days_across_year(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1947-01-03 23:59:59",  # Friday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_1.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 7)

    def test_number_days_across_year_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1947-01-03 23:59:59",  # Friday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 5)

    def test_number_of_hours_excluding_employee_2(self):
        self.holiday_type.write({"unit_of_measure": "hour", "request_unit": "hour"})
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 2)

    def test_number_days_excluding_as_employee_user(self):
        """Test an employee user excludes holidays using its public work address."""
        leave_request = self.HrLeave.with_user(self.employee_user).new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "work_entry_type_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )

        self.assertEqual(leave_request.number_of_days, 2)
