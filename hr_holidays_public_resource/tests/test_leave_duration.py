# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from .common import TestHolidaysPublicResourceCommon


class TestLeaveDuration(TestHolidaysPublicResourceCommon):
    """The standard duration engine has to see the public holidays."""

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.friday = self.monday + timedelta(days=4)
        self.wednesday = self.monday + timedelta(days=2)

    def test_full_week_without_public_holiday(self):
        leave = self._create_leave(self.employee, self.monday, self.friday)
        self.assertEqual(leave.number_of_days, 5)

    def test_public_holiday_shortens_the_leave(self):
        self._create_line(self.wednesday, name="Mid-week holiday")
        leave = self._create_leave(self.employee, self.monday, self.friday)
        self.assertEqual(leave.number_of_days, 4)

    def test_two_public_holidays_shorten_the_leave_twice(self):
        self._create_line(self.monday, name="First")
        self._create_line(self.wednesday, name="Second")
        leave = self._create_leave(self.employee, self.monday, self.friday)
        self.assertEqual(leave.number_of_days, 3)

    def test_leave_type_may_count_public_holidays(self):
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.leave_type.include_public_holidays_in_duration = True
        leave = self._create_leave(self.employee, self.monday, self.friday)
        self.assertEqual(leave.number_of_days, 5)

    def test_regional_holiday_only_shortens_the_regional_schedule(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        national = self._create_leave(self.employee, self.monday, self.friday)
        regional = self._create_leave(self.employee_by, self.monday, self.friday)
        self.assertEqual(national.number_of_days, 5)
        self.assertEqual(regional.number_of_days, 4)
