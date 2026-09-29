# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from .common import TestHolidaysPublicResourceCommon


class TestCalendarOverview(TestHolidaysPublicResourceCommon):
    """The working schedule overview also counts the regional days.

    A regional or region-scoped public holiday reaches a schedule through
    the people on it, so the overview resolves them from the employees'
    work locations.
    """

    def _overview(self, calendar):
        calendar.invalidate_recordset(["public_holiday_overview_line_ids"])
        return calendar.public_holiday_overview_line_ids

    def test_a_nationwide_line_shows_on_every_schedule(self):
        line = self._create_line(self._work_monday(), name="National")
        self.assertIn(line, self._overview(self.calendar))
        self.assertIn(line, self._overview(self.calendar_by))

    def test_a_regional_line_shows_on_the_employees_schedule(self):
        line = self._create_line(
            self._work_monday(), name="Fronleichnam", regions=self.region_by
        )
        self.assertIn(line, self._overview(self.calendar_by))
        self.assertNotIn(line, self._overview(self.calendar))

    def test_a_region_line_shows_on_the_employees_schedule(self):
        region = self._create_region("Augsburg")
        self.employee.work_location_id.public_holiday_region_id = region
        line = self._create_line(
            self._work_monday(),
            name="Friedensfest",
            regions=region,
        )
        self.assertIn(line, self._overview(self.calendar))
        self.assertNotIn(line, self._overview(self.calendar_by))

    def test_the_employee_opt_out_hides_the_regional_days(self):
        national = self._create_line(self._work_monday(), name="National")
        regional = self._create_line(
            self._work_monday() + timedelta(days=1),
            name="Fronleichnam",
            regions=self.region_by,
        )
        self.calendar_by.public_holiday_employee_sync = False
        overview = self._overview(self.calendar_by)
        self.assertNotIn(regional, overview)
        self.assertIn(national, overview, "the nationwide reach stays")
