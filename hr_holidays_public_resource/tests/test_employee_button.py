# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestHolidaysPublicResourceCommon


class TestEmployeeButton(TestHolidaysPublicResourceCommon):
    """The template says which employees it gives a day off."""

    def _count(self):
        self.holiday.invalidate_recordset(["employee_count", "resource_calendar_count"])
        return self.holiday.employee_count

    def test_no_line_reaches_nobody(self):
        self.assertEqual(self._count(), 0)
        self.assertFalse(self.holiday._get_applicable_employees())

    def test_a_nationwide_holiday_reaches_everybody(self):
        self._create_line(date(self.year, 10, 3), name="Nationwide")
        applicable = self.holiday._get_applicable_employees()
        # The company may hold employees beyond the fixtures, so the reach is
        # checked for inclusion rather than equality.
        self.assertIn(self.employee, applicable)
        self.assertIn(self.employee_by, applicable)
        self.assertEqual(self._count(), len(applicable))

    def test_a_regional_holiday_reaches_that_region_only(self):
        self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertEqual(self.holiday._get_applicable_employees(), self.employee_by)

    def test_a_colleague_sharing_the_schedule_is_left_out(self):
        """Regional public holidays follow the person, not their schedule."""
        sharing = self._create_employee(
            "Emp Nordrhein", self.calendar_by, self.region_nw
        )
        self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        applicable = self.holiday._get_applicable_employees()
        self.assertIn(self.employee_by, applicable)
        self.assertNotIn(sharing, applicable)

    def test_the_button_opens_exactly_those_employees(self):
        self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        action = self.holiday.action_view_employees()
        self.assertEqual(action["res_model"], "hr.employee")
        self.assertEqual(
            self.env["hr.employee"].search(action["domain"]), self.employee_by
        )

    def test_an_opted_out_schedule_drops_its_regional_employees(self):
        """The employee opt-out only stops the personal entries.

        A nationwide public holiday reaches everybody through the
        company-wide record whatever the schedule says, so only the regional
        reach follows the flag.
        """
        self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.calendar_by.public_holiday_employee_sync = False
        self.assertNotIn(self.employee_by, self.holiday._get_applicable_employees())

    def test_an_opted_out_schedule_keeps_its_nationwide_employees(self):
        self._create_line(date(self.year, 10, 3), name="Nationwide")
        self.calendar_by.public_holiday_employee_sync = False
        self.assertIn(self.employee_by, self.holiday._get_applicable_employees())
