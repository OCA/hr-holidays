# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.hr_holidays_public.tests import test_holidays_public


class TestHolidaysPublicBase(test_holidays_public.TestHolidaysPublicBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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


class TestHolidaysPublic(TestHolidaysPublicBase):
    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, state_ids=False, city_ids=False
    ):
        self.assertFalse(
            self.leave_model.with_user(self.env.ref("base.user_demo").id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")
            .get("2019-07-30", False)
        )
        holiday = self.holiday_model.create({"year": 2019, "country_id": country_id})
        self.holiday_model_line.create(
            {
                "name": "holiday x",
                "date": "2019-07-30",
                "year_id": holiday.id,
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
            state_ids=[(6, 0, [self.employee.address_id.state_id.id])],
            city_ids=[(6, 0, [self.employee.address_id.city_id.id])],
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
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
            city_ids=[(6, 0, [demo_user_empl_addr.city_id.id])],
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
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
            city_ids=[(6, 0, [self.us_city_b.id])],
        )

    def test_get_unusual_days_return_public_holidays_fallback_to_company_state_city(
        self,
    ):
        self.env.ref("base.user_demo").employee_id = False
        self.env.company.partner_id.city_id = self.us_city_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.company.country_id.id,
            state_ids=[(6, 0, [self.env.company.state_id.id])],
            city_ids=[(6, 0, [self.env.company.partner_id.city_id.id])],
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
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
            city_ids=[(6, 0, [self.us_city_b.id])],
        )
