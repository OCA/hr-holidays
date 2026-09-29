# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestLeaveOverHoliday(TestPublicResourceTimesheetCommon):
    """A public holiday appearing inside an approved leave re-books the day.

    The leave loses its entry for that day and the day is booked as public
    time off instead; moving the public holiday moves the booking, and
    removing it gives the leave its entry back. This has to hold for a
    regional public holiday, generated for the person alone, exactly as for
    a nationwide one.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)
        self.thursday = self.monday + timedelta(days=3)
        self.friday = self.monday + timedelta(days=4)

    def _leave_days(self, leave):
        return sorted(
            self.analytic_model.search([("holiday_id", "=", leave.id)]).mapped("date")
        )

    def _week_without(self, *days):
        return sorted(
            self.monday + timedelta(days=offset)
            for offset in range(5)
            if self.monday + timedelta(days=offset) not in days
        )

    def _assert_lifecycle(self, employee, regions):
        leave = self._create_leave(employee, self.monday, self.friday)
        self.assertEqual(self._leave_days(leave), self._week_without())

        line = self._create_line(self.wednesday, name="Holiday", regions=regions)
        self.assertEqual(leave.number_of_days, 4)
        self.assertEqual(self._leave_days(leave), self._week_without(self.wednesday))
        self.assertEqual(
            sum(self._lines_for(employee, self.wednesday).mapped("unit_amount")), 8.0
        )

        line.date = self.thursday
        self.assertEqual(leave.number_of_days, 4)
        self.assertEqual(self._leave_days(leave), self._week_without(self.thursday))
        self.assertFalse(self._lines_for(employee, self.wednesday))
        self.assertEqual(
            sum(self._lines_for(employee, self.thursday).mapped("unit_amount")), 8.0
        )

        line.unlink()
        self.assertEqual(leave.number_of_days, 5)
        self.assertEqual(self._leave_days(leave), self._week_without())
        self.assertFalse(self._lines_for(employee, self.thursday))

    def test_nationwide_public_holiday_over_a_leave(self):
        self._assert_lifecycle(self.employee, regions=None)

    def test_regional_public_holiday_over_a_leave(self):
        self._assert_lifecycle(self.employee_by, regions=self.region_by)

    def test_regional_public_holiday_leaves_other_people_alone(self):
        leave = self._create_leave(self.employee, self.monday, self.friday)
        self._create_line(self.wednesday, name="Holiday", regions=self.region_by)
        self.assertEqual(leave.number_of_days, 5)
        self.assertEqual(self._leave_days(leave), self._week_without())
        self.assertFalse(self._lines_for(self.employee, self.wednesday))
