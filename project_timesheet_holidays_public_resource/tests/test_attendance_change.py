# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestAttendanceChange(TestPublicResourceTimesheetCommon):
    """Changing the working hours refreshes the future holiday timesheets.

    The timesheet of a public holiday snapshots the working hours of its day.
    Removing a day from the schedule must delete the future entries of the
    holidays on it, and adding a day must create them; the past stays as it
    was booked.
    """

    def _future_line(self, weekday):
        """A public holiday on the next such weekday at least a week away."""
        day = fields.Date.today() + timedelta(days=7)
        while day.weekday() != weekday:
            day += timedelta(days=1)
        holiday = (
            self.holiday
            if day.year == self.year
            else self.holiday_model.create(
                {"year": day.year, "country_id": self.country.id}
            )
        )
        line = self.line_model.create(
            {"name": "Future holiday", "date": day, "public_holiday_id": holiday.id}
        )
        return line, day

    def _friday_attendances(self):
        return self.calendar.attendance_ids.filtered(
            lambda attendance: attendance.dayofweek == "4"
            and not attendance.display_type
        )

    def test_removing_the_day_deletes_the_future_timesheets(self):
        line, day = self._future_line(4)
        self.assertTrue(self._lines_for(self.employee, day))
        self._friday_attendances().unlink()
        self.assertFalse(self._lines_for(self.employee, day))
        # The other schedule still works Fridays and keeps its entry.
        self.assertTrue(self._lines_for(self.employee_by, day))

    def test_adding_the_day_creates_the_future_timesheets(self):
        line, day = self._future_line(4)
        self._friday_attendances().unlink()
        self.assertFalse(self._lines_for(self.employee, day))
        self.env["resource.calendar.attendance"].create(
            {
                "name": "Friday morning",
                "calendar_id": self.calendar.id,
                "dayofweek": "4",
                "day_period": "morning",
                "hour_from": 8,
                "hour_to": 12,
            }
        )
        lines = self._lines_for(self.employee, day)
        self.assertTrue(lines)
        self.assertEqual(sum(lines.mapped("unit_amount")), 4.0)

    def test_the_past_is_left_alone(self):
        past_day = self._work_monday()
        self._create_line(past_day, name="Past holiday")
        before = self._lines_for(self.employee, past_day)
        self.assertTrue(before)
        self._friday_attendances().unlink()
        self.assertEqual(self._lines_for(self.employee, past_day), before)
