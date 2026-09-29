# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import tagged

from .common import TestHolidaysPublicResourceCommon


@tagged("post_install", "-at_install")
class TestRegionalEffects(TestHolidaysPublicResourceCommon):
    """A regional public holiday has to behave like any other for its person.

    Standard reads the working time of a schedule with nobody on it, so
    everything keyed on that -- the grey days of a calendar, the leave
    durations -- passes a resource-level public holiday by unless it is told
    about it. The timesheet side of this lives in
    `project_timesheet_holidays_public_resource`.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)

    def _unusual(self, employee):
        return (
            self.env["hr.leave"]
            .with_context(employee_id=employee.id)
            .get_unusual_days(
                f"{self.monday} 00:00:00",
                f"{self.monday + timedelta(days=4)} 23:59:59",
            )
        )

    def test_the_day_is_greyed_out_for_that_person(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        key = fields.Date.to_string(self.wednesday)
        self.assertTrue(
            self._unusual(self.employee_by)[key],
            "the person's own public holiday has to show as a free day",
        )

    def test_the_day_stays_a_working_day_for_everybody_else(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        key = fields.Date.to_string(self.wednesday)
        self.assertFalse(self._unusual(self.employee)[key])

    def test_the_leave_duration_skips_it(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        leave = self._create_leave(
            self.employee_by, self.monday, self.monday + timedelta(days=4)
        )
        self.assertEqual(leave.number_of_days, 4)
