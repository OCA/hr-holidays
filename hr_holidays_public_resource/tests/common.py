# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import Command
from odoo.tests.common import TransactionCase


class TestHolidaysPublicResourceCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.year = date.today().year
        cls.holiday_model = cls.env["calendar.public.holiday"]
        cls.line_model = cls.env["calendar.public.holiday.line"]
        cls.leave_model = cls.env["resource.calendar.leaves"]

        cls.line_model.search([]).unlink()
        cls.holiday_model.search([]).unlink()
        cls.leave_model.search([("resource_id", "=", False)]).with_context(
            public_holiday_sync=True
        ).unlink()

        cls.country = cls.env.ref("base.de")
        # Nationwide public holidays are generated for every company whose
        # country matches -- and for companies without a country, which cannot
        # be ruled out. Pinning the bystander companies to an unrelated
        # country keeps them out of the fixtures' way.
        cls.env["res.company"].sudo().search([("id", "!=", cls.env.company.id)]).write(
            {"country_id": cls.env.ref("base.it").id}
        )
        # Two regions of the fixture country, shared by every company.
        cls.region_by = cls._create_region("Test Bayern", country=cls.country)
        cls.region_nw = cls._create_region("Test Nordrhein", country=cls.country)
        # The current company is reused rather than a fresh one: several
        # timesheet modules add required columns to res.company that a bare
        # create() does not fill in.
        cls.company = cls.env.company
        cls.company.country_id = cls.country

        cls.env["resource.calendar"].sudo().with_context(active_test=False).search(
            []
        ).write({"public_holiday_employee_sync": False})

        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Standard 40h",
                "company_id": cls.company.id,
                "tz": "Europe/Berlin",
            }
        )
        # The company works by this schedule, as in a real database. It is also
        # what falls back for users without an employee in the active company.
        cls.company.resource_calendar_id = cls.calendar
        cls.calendar_by = cls.env["resource.calendar"].create(
            {
                "name": "Standard 40h Bayern",
                "company_id": cls.company.id,
                "tz": "Europe/Berlin",
            }
        )

        cls.company_address = cls.env["res.partner"].create(
            {"name": "Head office", "country_id": cls.country.id}
        )
        # A scoped public holiday follows where the work is done, so the work
        # region of the employee is what puts them in Bayern.
        cls.employee = cls._create_employee("Emp National", cls.calendar)
        cls.employee_by = cls._create_employee(
            "Emp Bayern", cls.calendar_by, cls.region_by
        )

        cls.holiday = cls.holiday_model.create(
            {"year": cls.year, "country_id": cls.country.id}
        )

        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Paid Time Off",
                "requires_allocation": False,
                "leave_validation_type": "no_validation",
                "request_unit": "day",
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _create_work_location(cls, name, region=None):
        """A place of work standing for a region, which a holiday follows."""
        address = cls.env["res.partner"].create(
            {"name": f"{name} address", "country_id": cls.country.id}
        )
        return cls.env["hr.work.location"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "address_id": address.id,
                "public_holiday_region_id": region.id if region else False,
            }
        )

    @classmethod
    def _create_employee(cls, name, calendar, region=None, work_location=True):
        # The work address is the company's, as it usually is; the region
        # can only come from the work location.
        work_location = (
            cls._create_work_location(f"{name} office", region)
            if work_location
            else cls.env["hr.work.location"]
        )
        return cls.env["hr.employee"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "resource_calendar_id": calendar.id,
                "address_id": cls.company_address.id,
                "work_location_id": work_location.id,
                "tz": "Europe/Berlin",
                # Since odoo/odoo@45c601bf every day outside of an employee's
                # contract counts as an unusual day, so the fixtures need a
                # running contract for the greying-out assertions to mean
                # anything.
                "date_version": f"{cls.year - 1}-01-01",
                "contract_date_start": f"{cls.year - 1}-01-01",
            }
        )

    @classmethod
    def _create_region(cls, name, company=None, country=None):
        """A public holiday region, the label days are assigned by."""
        return cls.env["calendar.public.holiday.region"].create(
            {
                "name": name,
                "company_id": company.id if company else False,
                "country_id": country.id if country else False,
            }
        )

    @classmethod
    def _create_line(cls, day, name="Holiday", regions=None):
        return cls.line_model.create(
            {
                "name": name,
                "date": day,
                "public_holiday_id": cls.holiday.id,
                "region_ids": ([Command.set(regions.ids)] if regions else False),
            }
        )

    def _create_leave(self, employee, date_from, date_to, leave_type=None):
        return self.env["hr.leave"].create(
            {
                "name": "Vacation",
                "employee_id": employee.id,
                "holiday_status_id": (leave_type or self.leave_type).id,
                "request_date_from": date_from,
                "request_date_to": date_to,
            }
        )

    @classmethod
    def _work_monday(cls):
        """A Monday well inside the current year.

        The whole week is then made of working days, and the public holiday
        line stays in the year of its calendar, which is constrained.
        """
        day = date(cls.year, 3, 1)
        while day.weekday() != 0:
            day += timedelta(days=1)
        return day
