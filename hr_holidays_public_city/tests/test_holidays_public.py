# Copyright 2023-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.calendar_public_holiday.tests.test_calendar_public_holiday import (
    TestCalendarPublicHoliday,
)


class TestHolidaysPublic(TestCalendarPublicHoliday):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_model = cls.env["hr.employee"]
        cls.leave_model = cls.env["hr.leave"]
        cls.st_state_1 = cls.env["res.country.state"].create(
            {"name": "DE State 1", "code": "de", "country_id": cls.country_1.id}
        )
        cls.st_state_2 = cls.env["res.country.state"].create(
            {"name": "ST State 2", "code": "st", "country_id": cls.country_1.id}
        )
        cls.employee = cls.employee_model.create(
            {
                "name": "Employee 1",
                "address_id": cls.res_partner.id,
            }
        )
        cls.us_city_a = cls.env["res.city"].create(
            {
                "name": "Test city A",
                "state_id": cls.env.ref("base.state_us_4").id,
                "country_id": cls.env.ref("base.us").id,
            }
        )
        cls.us_city_b = cls.env["res.city"].create(
            {
                "name": "Test city B",
                "state_id": cls.env.ref("base.state_us_4").id,
                "country_id": cls.env.ref("base.us").id,
            }
        )

    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, state_ids=False, city_ids=False
    ):
        self.assertFalse(
            self.leave_model.with_user(self.env.ref("base.user_demo").id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")
            .get("2019-07-30", False)
        )
        holiday = self.holiday_model.create({"year": 2019, "country_id": country_id})
        self.holiday_line_model.create(
            {
                "name": "holiday x",
                "date": "2019-07-30",
                "public_holiday_id": holiday.id,
                "state_ids": state_ids,
                "city_ids": city_ids,
            }
        )
        self.assertEqual(
            self.leave_model.with_user(
                self.env.ref("base.user_demo").id
            ).get_unusual_days("2019-07-01", date_to="2019-07-31")["2019-07-30"],
            expected,
        )

    def test_public_holidays_context(self):
        self.env.ref("base.user_demo").employee_id.address_id.country_id = False
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.ref("base.user_demo").employee_id.address_id.city_id = False
        self.employee.address_id.country_id = self.env.ref("base.us")
        self.employee.address_id.state_id = self.env.ref("base.state_us_4")
        self.employee.address_id.city_id = self.us_city_a
        self.leave_model = self.leave_model.with_context(employee_id=self.employee.id)
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[Command.set(self.employee.address_id.state_id.ids)],
            city_ids=[Command.set(self.employee.address_id.city_id.ids)],
        )

    def test_get_unusual_days_return_public_holidays_same_state_same_city(self):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl_addr.city_id = self.us_city_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[Command.set(demo_user_empl_addr.state_id.ids)],
            city_ids=[Command.set(demo_user_empl_addr.city_id.ids)],
        )

    def test_get_unusual_days_return_public_holidays_same_state_differente_city(self):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl_addr.city_id = self.us_city_a
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[Command.set(demo_user_empl_addr.state_id.ids)],
            city_ids=[Command.set(self.us_city_b.ids)],
        )

    def test_get_unusual_days_return_public_holidays_fallback_to_company_state_city(
        self,
    ):
        self.env.ref("base.user_demo").employee_id = False
        self.env.company.partner_id.city_id = self.us_city_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.company.country_id.id,
            state_ids=[Command.set(self.env.company.state_id.ids)],
            city_ids=[Command.set(self.env.company.partner_id.city_id.ids)],
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_state_city(
        self,
    ):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.city_id = False
        self.env.company.partner_id.city_id = self.us_city_a
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=demo_user_empl_addr.country_id.id,
            state_ids=[Command.set(demo_user_empl_addr.state_id.ids)],
            city_ids=[Command.set(self.us_city_b.ids)],
        )
