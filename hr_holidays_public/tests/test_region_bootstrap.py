# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.hr_holidays_public.hooks import (
    bootstrap_regions,
    create_regions_from_work_locations,
)


class TestRegionBootstrapCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.country = cls.env["res.country"].create(
            {"name": "Bootstrap Country", "code": "XB"}
        )
        cls.region_model = cls.env["calendar.public.holiday.region"]

    @classmethod
    def _create_work_location(cls, name, state=None, company=None, country=True):
        address = cls.env["res.partner"].create(
            {
                "name": f"{name} address",
                "country_id": cls.country.id if country else False,
                "state_id": state.id if state else False,
            }
        )
        return cls.env["hr.work.location"].create(
            {
                "name": name,
                "company_id": (company or cls.company).id,
                "address_id": address.id,
            }
        )

    @classmethod
    def _create_employee(cls, name, work_location):
        return cls.env["hr.employee"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "work_location_id": work_location.id if work_location else False,
            }
        )


class TestRegionBootstrap(TestRegionBootstrapCommon):
    """Installing the module builds the regions from the work locations.

    One public holiday region per work location, named after it, owned by
    its company and carrying the country of its address, with everybody
    assigned through the work location of their versions.
    """

    def test_one_region_per_work_location(self):
        address = self.env["res.partner"].create(
            {"name": "Shared office address", "country_id": self.country.id}
        )
        first = self.env["hr.work.location"].create(
            {
                "name": "Front office",
                "company_id": self.company.id,
                "address_id": address.id,
            }
        )
        second = self.env["hr.work.location"].create(
            {
                "name": "Back office",
                "company_id": self.company.id,
                "address_id": address.id,
            }
        )
        created = create_regions_from_work_locations(self.env)
        self.assertEqual(len(created), 2, "one region per work location")
        self.assertNotEqual(
            first.public_holiday_region_id,
            second.public_holiday_region_id,
            "a shared address does not make a shared region",
        )
        self.assertEqual(first.public_holiday_region_id.name, "Front office")
        self.assertEqual(second.public_holiday_region_id.name, "Back office")
        for region in created:
            self.assertEqual(region.company_id, self.company)
            self.assertEqual(region.country_id, self.country, "the address country")

    def test_a_region_always_carries_a_company(self):
        office = self._create_work_location("Office")
        create_regions_from_work_locations(self.env)
        self.assertEqual(office.public_holiday_region_id.company_id, office.company_id)

    def test_an_address_without_a_country_takes_the_company_country(self):
        self.company.country_id = self.country
        office = self._create_work_location("Office", country=False)
        create_regions_from_work_locations(self.env)
        self.assertEqual(office.public_holiday_region_id.country_id, self.country)

    def test_employees_are_assigned_through_their_work_location(self):
        office = self._create_work_location("Office")
        employee = self._create_employee("Emp Office", office)
        create_regions_from_work_locations(self.env)
        self.assertTrue(employee.public_holiday_region_id)
        self.assertEqual(
            employee.public_holiday_region_id, office.public_holiday_region_id
        )

    def test_the_assignment_follows_a_relinked_work_location(self):
        office = self._create_work_location("Office")
        employee = self._create_employee("Emp Office", office)
        create_regions_from_work_locations(self.env)
        moved = self.region_model.create({"name": "Moved"})
        office.public_holiday_region_id = moved
        self.assertEqual(
            employee.public_holiday_region_id,
            moved,
            "the employee follows the work location's public holiday region",
        )

    def test_the_bootstrap_is_idempotent(self):
        self._create_work_location("Office")
        created = create_regions_from_work_locations(self.env)
        self.assertTrue(created)
        self.assertFalse(
            create_regions_from_work_locations(self.env),
            "a second run finds every work location already linked",
        )

    def test_an_employee_without_a_work_location_stays_unassigned(self):
        loner = self._create_employee("Emp Loner", None)
        create_regions_from_work_locations(self.env)
        self.assertFalse(loner.public_holiday_region_id)


class TestLegacyStateBootstrap(TestRegionBootstrapCommon):
    """The former state-scoped public holidays reach the regions in the state.

    ``calendar_public_holiday`` keeps the states its lines used to be scoped
    to; once the regions of the work locations exist, those lines are
    assigned to the regions of the work locations whose address lies in
    one of their states.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.state_by = cls.env["res.country.state"].create(
            {"name": "Bootstrap Bayern", "code": "TBY", "country_id": cls.country.id}
        )
        cls.state_nw = cls.env["res.country.state"].create(
            {"name": "Bootstrap Nordrhein", "code": "TNW", "country_id": cls.country.id}
        )
        cls.holiday = cls.env["calendar.public.holiday"].create(
            {"year": 2025, "country_id": cls.country.id}
        )
        cls.line_by = cls.env["calendar.public.holiday.line"].create(
            {
                "name": "Fronleichnam",
                "date": date(2025, 6, 19),
                "public_holiday_id": cls.holiday.id,
            }
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

    def test_the_line_reaches_the_work_locations_in_its_state(self):
        munich = self._create_work_location("Munich office", self.state_by)
        cologne = self._create_work_location("Cologne office", self.state_nw)
        self._plant_legacy_state(self.line_by, self.state_by)
        bootstrap_regions(self.env)
        self.assertEqual(self.line_by.region_ids, munich.public_holiday_region_id)
        self.assertNotIn(cologne.public_holiday_region_id, self.line_by.region_ids)
        self.assertTrue(self.line_by.active)

    def test_two_work_locations_in_the_state_both_get_the_line(self):
        munich = self._create_work_location("Munich office", self.state_by)
        nuremberg = self._create_work_location("Nuremberg office", self.state_by)
        self._plant_legacy_state(self.line_by, self.state_by)
        bootstrap_regions(self.env)
        self.assertEqual(
            self.line_by.region_ids,
            munich.public_holiday_region_id | nuremberg.public_holiday_region_id,
        )

    def test_a_line_nobody_works_in_stays_disabled(self):
        """The base module disabled it; nothing here enables it."""
        self._create_work_location("Cologne office", self.state_nw)
        self._plant_legacy_state(self.line_by, self.state_by)
        self.line_by.active = False
        bootstrap_regions(self.env)
        self.assertFalse(self.line_by.region_ids)
        self.assertFalse(self.line_by.active)

    def test_the_bootstrap_enables_a_line_it_gives_a_region(self):
        self._create_work_location("Munich office", self.state_by)
        self._plant_legacy_state(self.line_by, self.state_by)
        self.line_by.active = False
        bootstrap_regions(self.env)
        self.assertTrue(self.line_by.active)


@tagged("post_install", "-at_install")
class TestRegionBootstrapCompany(TestRegionBootstrapCommon):
    """Run once everything is loaded: creating a company needs the defaults
    other modules add to ``res.company``."""

    def test_a_work_location_of_another_company_gets_its_company(self):
        other = self.env["res.company"].create({"name": "Other Co"})
        office = self._create_work_location("Branch office", company=other)
        create_regions_from_work_locations(self.env)
        self.assertEqual(office.public_holiday_region_id.company_id, other)
