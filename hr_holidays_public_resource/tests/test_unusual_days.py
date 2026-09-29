# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields

from .common import TestHolidaysPublicResourceCommon


class TestUnusualDays(TestHolidaysPublicResourceCommon):
    """Greying out is left entirely to resource.calendar._get_unusual_days."""

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)

    def _unusual_days(self, employee):
        # get_unusual_days parses datetime strings, not plain dates.
        return (
            self.env["hr.leave"]
            .with_context(employee_id=employee.id)
            .get_unusual_days(
                f"{self.monday} 00:00:00",
                f"{self.monday + timedelta(days=6)} 23:59:59",
            )
        )

    def test_working_day_is_usual_without_public_holiday(self):
        self.assertFalse(
            self._unusual_days(self.employee)[fields.Date.to_string(self.wednesday)]
        )

    def test_public_holiday_is_an_unusual_day(self):
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertTrue(
            self._unusual_days(self.employee)[fields.Date.to_string(self.wednesday)]
        )

    def test_weekend_stays_unusual(self):
        saturday = self.monday + timedelta(days=5)
        self.assertTrue(
            self._unusual_days(self.employee)[fields.Date.to_string(saturday)]
        )

    def test_regional_holiday_is_unusual_only_for_that_schedule(self):
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        key = fields.Date.to_string(self.wednesday)
        self.assertFalse(self._unusual_days(self.employee)[key])
        self.assertTrue(self._unusual_days(self.employee_by)[key])
