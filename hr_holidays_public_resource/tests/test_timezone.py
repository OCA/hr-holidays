# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

import pytz

from odoo import Command

from .common import TestHolidaysPublicResourceCommon


class TestTimezone(TestHolidaysPublicResourceCommon):
    """Regression tests for hr_holidays._prepare_public_holidays_values.

    That hook only exists once ``hr_holidays`` is installed, and it rewrites
    the wall clock of a global time off carrying a schedule on create using
    ``self.env.user.tz``. Only the own entries of a schedule are affected --
    company-wide and personal records never see the hook -- so these tests
    run on the schedule-carrying entries of lines listing a schedule.
    """

    def _assert_local_full_day(self, leave, day, tz_name):
        tz = pytz.timezone(tz_name)
        start = pytz.utc.localize(leave.date_from).astimezone(tz)
        stop = pytz.utc.localize(leave.date_to).astimezone(tz)
        self.assertEqual(start.date(), day, f"start {start} is not on {day}")
        self.assertEqual((start.hour, start.minute), (0, 0))
        self.assertEqual(stop.date(), day, f"stop {stop} is not on {day}")
        self.assertEqual((stop.hour, stop.minute), (23, 59))

    def test_native_timezone_hook_is_present(self):
        self.assertTrue(
            self.line_model._has_native_public_holiday_tz_shift(),
            "hr_holidays should provide _prepare_public_holidays_values",
        )

    def _sync_and_get(self, calendar, day):
        # A regional line listing the schedule: the schedule-carrying entries
        # are the only generated records the native create hook touches.
        line = self.line_model.create(
            {
                "name": "Timezone check",
                "date": day,
                "public_holiday_id": self.holiday.id,
                "region_ids": [Command.set(self.region_nw.ids)],
                "additional_resource_calendar_ids": [Command.set(calendar.ids)],
            }
        )
        return self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("calendar_id", "=", calendar.id),
            ]
        )

    def test_calendar_ahead_of_the_user(self):
        self.env.user.tz = "Europe/Berlin"
        calendar = self.env["resource.calendar"].create(
            {
                "name": "Auckland",
                "company_id": self.company.id,
                "tz": "Pacific/Auckland",
            }
        )
        day = self._work_monday()
        self._assert_local_full_day(
            self._sync_and_get(calendar, day), day, "Pacific/Auckland"
        )

    def test_calendar_behind_the_user(self):
        self.env.user.tz = "Pacific/Auckland"
        calendar = self.env["resource.calendar"].create(
            {
                "name": "Los Angeles",
                "company_id": self.company.id,
                "tz": "America/Los_Angeles",
            }
        )
        day = self._work_monday() + timedelta(days=1)
        self._assert_local_full_day(
            self._sync_and_get(calendar, day), day, "America/Los_Angeles"
        )

    def test_user_without_timezone(self):
        self.env.user.tz = False
        day = self._work_monday() + timedelta(days=2)
        self._assert_local_full_day(
            self._sync_and_get(self.calendar, day), day, "Europe/Berlin"
        )

    def test_matching_timezones(self):
        self.env.user.tz = "Europe/Berlin"
        day = self._work_monday() + timedelta(days=3)
        self._assert_local_full_day(
            self._sync_and_get(self.calendar, day), day, "Europe/Berlin"
        )

    def test_regional_mirror_in_the_resource_timezone(self):
        """Personal mirrors never see the native create hook at all."""
        self.env.user.tz = "America/New_York"
        day = self._work_monday() + timedelta(days=4)
        line = self._create_line(day, name="Regional check", regions=self.region_by)
        mirror = self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("resource_id", "=", self.employee_by.resource_id.id),
            ]
        )
        self.assertEqual(len(mirror), 1)
        self.assertEqual(self.employee_by.resource_id.tz, "Europe/Berlin")
        self._assert_local_full_day(mirror, day, "Europe/Berlin")
