# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.hr_holidays_public.hooks import bootstrap_regions

from .common import TestHolidaysPublicResourceCommon


class TestLegacyStateBootstrapSync(TestHolidaysPublicResourceCommon):
    """The bootstrap generates the days of the former state-scoped holidays.

    The bootstrap itself lives in ``hr_holidays_public`` and is tested
    there; what is asserted here is that the people it puts into a region
    get that region's public holidays generated.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.state_by = cls.env["res.country.state"].create(
            {"name": "Bootstrap Bayern", "code": "TBY", "country_id": cls.country.id}
        )

    def _work_location_in(self, name, state):
        address = self.env["res.partner"].create(
            {
                "name": f"{name} address",
                "country_id": self.country.id,
                "state_id": state.id,
            }
        )
        return self.env["hr.work.location"].create(
            {"name": name, "company_id": self.company.id, "address_id": address.id}
        )

    def _plant_legacy_state(self, line, state):
        self.env.cr.execute("DROP TABLE IF EXISTS public_holiday_state_rel")
        self.env.cr.execute(
            "CREATE TABLE public_holiday_state_rel "
            "(public_holiday_line_id integer, state_id integer)"
        )
        self.env.cr.execute(
            "INSERT INTO public_holiday_state_rel VALUES (%s, %s)",
            (line.id, state.id),
        )

    def test_the_people_working_there_get_the_state_holidays(self):
        line = self._create_line(self._work_monday(), name="Fronleichnam")
        self._plant_legacy_state(line, self.state_by)
        office = self._work_location_in("Munich office", self.state_by)
        hired = self.env["hr.employee"].create(
            {
                "name": "Emp Munich",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar_by.id,
                "work_location_id": office.id,
                "date_version": f"{self.year - 1}-01-01",
                "contract_date_start": f"{self.year - 1}-01-01",
            }
        )
        bootstrap_regions(self.env)
        self.assertEqual(line.region_ids, office.public_holiday_region_id)
        self.assertTrue(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("resource_id", "=", hired.resource_id.id),
                ]
            )
        )
        self.assertFalse(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("resource_id", "=", self.employee.resource_id.id),
                ]
            ),
            "somebody outside the state is not concerned",
        )
