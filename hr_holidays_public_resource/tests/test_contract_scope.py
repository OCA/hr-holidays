# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestHolidaysPublicResourceCommon


class TestContractScope(TestHolidaysPublicResourceCommon):
    """Personal public holidays follow the contract valid on their day.

    The work location and the working schedule live on the version, so a
    contract change in October moves the October holidays without touching
    the March ones -- and a day no contract covers is given to nobody.
    """

    def _mirror(self, line, employee):
        return self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("resource_id", "=", employee.resource_id.id),
            ]
        )

    def test_a_future_version_moves_only_its_period(self):
        nw_office = self._create_work_location("NW office", self.region_nw)
        self.employee_by.create_version(
            {
                "date_version": date(self.year, 10, 1),
                "work_location_id": nw_office.id,
            }
        )
        spring_by = self._create_line(
            self._work_monday(), name="BY spring", regions=self.region_by
        )
        autumn_by = self._create_line(
            date(self.year, 10, 15), name="BY autumn", regions=self.region_by
        )
        autumn_nw = self._create_line(
            date(self.year, 10, 16), name="NW autumn", regions=self.region_nw
        )
        self.assertTrue(
            self._mirror(spring_by, self.employee_by),
            "the spring day follows the current Bavarian contract",
        )
        self.assertFalse(
            self._mirror(autumn_by, self.employee_by),
            "in October the employee no longer works in Bavaria",
        )
        self.assertTrue(
            self._mirror(autumn_nw, self.employee_by),
            "in October the employee works in Nordrhein",
        )

    def test_the_version_calendar_carries_the_mirror(self):
        self.employee_by.create_version(
            {
                "date_version": date(self.year, 10, 1),
                "resource_calendar_id": self.calendar.id,
            }
        )
        autumn = self._create_line(
            date(self.year, 10, 15), name="BY autumn", regions=self.region_by
        )
        mirror = self._mirror(autumn, self.employee_by)
        self.assertEqual(
            mirror.calendar_id,
            self.calendar,
            "the mirror carries the schedule of the version valid that day",
        )

    def test_a_day_after_the_contract_end_is_given_to_nobody(self):
        line = self._create_line(
            date(self.year, 10, 15), name="BY autumn", regions=self.region_by
        )
        self.assertTrue(self._mirror(line, self.employee_by))
        self.employee_by.version_id.contract_date_end = date(self.year, 9, 30)
        self.assertFalse(self._mirror(line, self.employee_by))
        # A day inside the contract stays.
        spring = self._create_line(
            self._work_monday(), name="BY spring", regions=self.region_by
        )
        self.assertTrue(self._mirror(spring, self.employee_by))

    def test_no_contract_no_public_holiday(self):
        region = self._create_work_location("Casual office", self.region_by)
        casual = self.env["hr.employee"].create(
            {
                "name": "Emp Casual",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar_by.id,
                "address_id": self.company_address.id,
                "work_location_id": region.id,
                "tz": "Europe/Berlin",
            }
        )
        line = self._create_line(
            self._work_monday(), name="Fronleichnam", regions=self.region_by
        )
        self.assertFalse(
            self._mirror(line, casual),
            "no contract means no public holiday",
        )
        self.assertTrue(self._mirror(line, self.employee_by))
