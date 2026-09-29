# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestTimesheet(TestPublicResourceTimesheetCommon):
    """Public holidays have to produce a timesheet entry.

    This is entirely standard `project_timesheet_holidays` behaviour, driven by
    the generated global time off; the point is that it now fires for the
    public holidays configured through the OCA calendar.
    """

    def test_public_holiday_generates_a_timesheet(self):
        day = self._work_monday()
        self._create_line(day, name="Public holiday")
        lines = self._lines_for(self.employee, day)
        self.assertTrue(lines, "no timesheet generated for the public holiday")
        self.assertEqual(sum(lines.mapped("unit_amount")), 8.0)

    def test_removing_the_public_holiday_removes_the_timesheet(self):
        day = self._work_monday() + timedelta(days=1)
        line = self._create_line(day, name="Public holiday")
        self.assertTrue(self._lines_for(self.employee, day))
        line.unlink()
        self.assertFalse(self._lines_for(self.employee, day))

    def test_a_leave_cannot_be_booked_on_a_public_holiday_alone(self):
        """Standard refuses a leave that would cost nothing."""
        day = self._work_monday() + timedelta(days=2)
        self._create_line(day, name="Public holiday")
        with self.assertRaises(ValidationError):
            self._create_leave(self.employee, day, day)
        self.assertEqual(
            len(self._lines_for(self.employee, day)),
            1,
            "the public holiday still accounts for the day",
        )

    def _week_lines(self, employee, monday):
        return self.analytic_model.search(
            [
                ("employee_id", "=", employee.id),
                ("date", ">=", monday),
                ("date", "<=", monday + timedelta(days=4)),
            ]
        )

    def test_public_holiday_over_an_approved_leave_adapts_its_timesheets(self):
        """The user scenario: the holiday is added after the leave is approved."""
        monday = self._work_monday()
        wednesday = monday + timedelta(days=2)
        leave = self._create_leave(self.employee, monday, monday + timedelta(days=4))
        self.assertEqual(leave.state, "validate")
        self.assertEqual(leave.number_of_days, 5)
        self.assertEqual(
            sum(self._week_lines(self.employee, monday).mapped("unit_amount")), 40
        )

        self._create_line(wednesday, name="Public holiday")

        self.assertEqual(leave.number_of_days, 4, "the leave costs one day less")
        week = self._week_lines(self.employee, monday)
        self.assertEqual(
            len(week.filtered(lambda line: line.holiday_id == leave)),
            4,
            "the leave must no longer be timesheeted on the public holiday",
        )
        self.assertEqual(
            len(self._lines_for(self.employee, wednesday)),
            1,
            "the public holiday has to account for that day instead",
        )
        self.assertEqual(
            sum(week.mapped("unit_amount")), 40, "the week is still fully accounted"
        )

    def test_removing_the_public_holiday_restores_the_leave_timesheets(self):
        monday = self._work_monday()
        wednesday = monday + timedelta(days=2)
        leave = self._create_leave(self.employee, monday, monday + timedelta(days=4))
        line = self._create_line(wednesday, name="Public holiday")
        line.unlink()
        self.assertEqual(leave.number_of_days, 5)
        week = self._week_lines(self.employee, monday)
        self.assertEqual(len(week.filtered(lambda t: t.holiday_id == leave)), 5)
        self.assertEqual(sum(week.mapped("unit_amount")), 40)
