# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestScheduleEntryTimesheet(TestPublicResourceTimesheetCommon):
    """The entry of a listed working schedule timesheets that schedule only.

    Only a regional line gets such an entry; a nationwide one is covered by
    its company-wide record. The region here is one nobody works in, so
    the schedule entry is the only record generated.
    """

    def _schedule_line(self, day, calendar):
        holiday = (
            self.holiday
            if day.year == self.year
            else self.holiday_model.create(
                {"year": day.year, "country_id": self.country.id}
            )
        )
        return self.line_model.create(
            {
                "name": "Shift day",
                "date": day,
                "public_holiday_id": holiday.id,
                "region_ids": [Command.set(self.region_nw.ids)],
                "additional_resource_calendar_ids": [Command.set(calendar.ids)],
            }
        )

    def test_schedule_entry_timesheets_only_its_schedule(self):
        day = self._work_monday()
        line = self._schedule_line(day, self.employee.resource_calendar_id)
        mirrors = self.leave_model.search([("public_holiday_line_id", "=", line.id)])
        self.assertEqual(len(mirrors), 1, "one entry carrying the schedule")
        self.assertTrue(mirrors.calendar_id)
        lines = self._lines_for(self.employee, day)
        self.assertEqual(len(lines), 1, "one timesheet entry for the schedule")
        self.assertEqual(sum(lines.mapped("unit_amount")), 8.0)
        self.assertFalse(
            self._lines_for(self.employee_by, day),
            "another schedule is not concerned",
        )

    def test_new_hire_backfill_is_not_doubled(self):
        """Standard back-fills future holidays on hiring, exactly once."""
        day = fields.Date.today() + timedelta(days=7)
        while day.weekday() != 0:
            day += timedelta(days=1)
        self._schedule_line(day, self.employee.resource_calendar_id)
        hired = self._create_employee("Emp Hired", self.employee.resource_calendar_id)
        lines = self._lines_for(hired, day)
        self.assertEqual(len(lines), 1, "one timesheet entry, not two")
