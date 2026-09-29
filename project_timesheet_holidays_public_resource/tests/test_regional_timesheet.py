# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestRegionalTimesheet(TestPublicResourceTimesheetCommon):
    """A regional public holiday has to be timesheeted like any other.

    Standard only timesheets company-wide time off, so a public holiday
    generated for a single resource passes `project_timesheet_holidays` by
    unless this module tells it about it.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)

    def test_a_timesheet_is_generated_for_that_person(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        lines = self._lines_for(self.employee_by, self.wednesday)
        self.assertTrue(lines, "no timesheet for the regional public holiday")
        self.assertEqual(sum(lines.mapped("unit_amount")), 8.0)

    def test_no_timesheet_for_anybody_else(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        self.assertFalse(
            self.analytic_model.search(
                [
                    ("employee_id", "=", self.employee.id),
                    ("date", "=", self.wednesday),
                ]
            )
        )

    def test_a_new_hire_gets_the_future_ones_timesheeted(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        hired = self._create_employee("Late Hire", self.calendar_by, self.region_by)
        self.assertTrue(
            self.analytic_model.search(
                [("employee_id", "=", hired.id), ("date", "=", self.wednesday)]
            ),
            "hiring has to back-fill the person's own public holidays",
        )
