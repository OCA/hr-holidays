# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestHolidaysPublicResourceCommon


class TestEmployeeRegions(TestHolidaysPublicResourceCommon):
    """Scoped public holidays belong to people, nationwide ones to schedules."""

    def _mirrors(self, line, calendar=None, resource=None):
        domain = [("public_holiday_line_id", "=", line.id)]
        if calendar is not None:
            domain.append(("calendar_id", "=", calendar.id))
        if resource is not None:
            domain.append(("resource_id", "=", resource.id if resource else False))
        return self.leave_model.search(domain)

    def test_a_regional_holiday_is_generated_for_the_person(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        mirrors = self._mirrors(line)
        self.assertEqual(mirrors.resource_id, self.employee_by.resource_id)
        self.assertEqual(mirrors.calendar_id, self.calendar_by)

    def test_a_regional_holiday_is_not_company_wide(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertFalse(
            self._mirrors(line, resource=False),
            "a regional public holiday must not reach the whole schedule",
        )

    def test_a_colleague_in_another_region_is_left_out(self):
        """The reason for generating per person rather than per schedule."""
        colleague = self._create_employee(
            "Emp Nordrhein", self.calendar_by, self.region_nw
        )
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        resources = self._mirrors(line).resource_id
        self.assertIn(self.employee_by.resource_id, resources)
        self.assertNotIn(colleague.resource_id, resources)

    def test_a_nationwide_holiday_is_company_wide(self):
        line = self._create_line(date(self.year, 10, 3), name="Nationwide")
        mirrors = self._mirrors(line)
        self.assertFalse(mirrors.resource_id, "nobody in particular")
        self.assertFalse(mirrors.calendar_id, "no working hours either")
        self.assertIn(self.company, mirrors.company_id)

    def test_a_nationwide_holiday_wins_over_a_regional_one(self):
        """Both would give the day off twice and be timesheeted twice."""
        day = date(self.year, 10, 3)
        regional = self._create_line(day, name="Regional", regions=self.region_by)
        national = self._create_line(day, name="Nationwide")
        self.assertFalse(self._mirrors(regional))
        self.assertIn(self.company, self._mirrors(national).company_id)

    def test_relinking_the_work_location_resyncs_on_its_own(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_nw
        )
        self.assertFalse(self._mirrors(line))
        self.employee_by.work_location_id.public_holiday_region_id = self.region_nw
        self.assertEqual(self._mirrors(line).resource_id, self.employee_by.resource_id)

    def test_moving_someone_to_another_work_location_resyncs_on_its_own(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_nw
        )
        self.assertFalse(self._mirrors(line))
        self.employee_by.work_location_id = self._create_work_location(
            "Nordrhein office", self.region_nw
        )
        self.assertEqual(self._mirrors(line).resource_id, self.employee_by.resource_id)

    def test_someone_without_a_work_location_is_left_out(self):
        nomad = self._create_employee(
            "Emp Nowhere", self.calendar_by, work_location=False
        )
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertNotIn(nomad.resource_id, self._mirrors(line).resource_id)

    def test_hiring_into_a_region_resyncs_on_its_own(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_nw
        )
        self.assertFalse(self._mirrors(line))
        hired = self._create_employee("Emp Nordrhein", self.calendar, self.region_nw)
        self.assertEqual(self._mirrors(line).resource_id, hired.resource_id)

    def test_an_employee_without_a_region_gets_nationwide_only(self):
        regional = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        national = self._create_line(date(self.year, 10, 3), name="Nationwide")
        self.assertNotIn(self.employee.resource_id, self._mirrors(regional).resource_id)
        self.assertIn(self.company, self._mirrors(national).company_id)
