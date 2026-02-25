# Copyright 2023-2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import new_test_user

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
        cls.user = new_test_user(
            cls.env,
            login="test-user_us_city_a",
        )
        cls.user.action_create_employee()
        cls.employee = cls.user.employee_id
        cls.address = cls.env["res.partner"].create(
            {
                "name": "Test address",
            }
        )
        cls.employee.address_id = cls.address
        cls.us_country = cls.env.ref("base.us")
        cls.state_us_4 = cls.env.ref("base.state_us_4")
        cls.us_city_a = cls.env["res.city"].create(
            {
                "name": "Test city A",
                "state_id": cls.state_us_4.id,
                "country_id": cls.us_country.id,
            }
        )
        cls.us_city_b = cls.env["res.city"].create(
            {
                "name": "Test city B",
                "state_id": cls.state_us_4.id,
                "country_id": cls.us_country.id,
            }
        )
        cls.holiday_model.create(
            {
                "year": 2019,
                "country_id": cls.us_country.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "holiday city a + b",
                            "date": "2019-07-29",
                            "state_ids": [Command.set(cls.state_us_4.ids)],
                            "city_ids": [
                                Command.set((cls.us_city_a + cls.us_city_b).ids)
                            ],
                        },
                    ),
                    Command.create(
                        {
                            "name": "holiday city a",
                            "date": "2019-07-30",
                            "state_ids": [Command.set(cls.state_us_4.ids)],
                            "city_ids": [Command.set(cls.us_city_a.ids)],
                        }
                    ),
                ],
            }
        )

    def test_public_holidays_context(self):
        self.address.country_id = False
        self.address.state_id = False
        self.address.city_id = False
        unusual_days = self.leave_model.with_user(self.user.id).get_unusual_days(
            "2019-07-01", date_to="2019-07-31"
        )
        self.assertFalse(unusual_days["2019-07-29"])
        self.assertFalse(unusual_days["2019-07-30"])
        self.assertFalse(unusual_days["2019-07-31"])

    def test_get_unusual_days_return_public_holidays_same_state_same_city(self):
        self.address.country_id = self.us_country
        self.address.state_id = self.state_us_4
        self.address.city_id = self.us_city_a
        unusual_days = self.leave_model.with_user(self.user.id).get_unusual_days(
            "2019-07-01", date_to="2019-07-31"
        )
        self.assertTrue(unusual_days["2019-07-29"])
        self.assertTrue(unusual_days["2019-07-30"])
        self.assertFalse(unusual_days["2019-07-31"])

    def test_get_unusual_days_return_public_holidays_same_state_differente_city(self):
        self.address.country_id = self.us_country
        self.address.state_id = self.state_us_4
        self.address.city_id = self.us_city_b
        unusual_days = self.leave_model.with_user(self.user.id).get_unusual_days(
            "2019-07-01", date_to="2019-07-31"
        )
        self.assertTrue(unusual_days["2019-07-29"])
        self.assertFalse(unusual_days["2019-07-30"])
        self.assertFalse(unusual_days["2019-07-31"])

    def test_get_unusual_days_return_public_holidays_fallback_to_company_state_city(
        self,
    ):
        self.user.employee_id = False
        self.user.company_id.partner_id.country_id = self.us_country
        self.user.company_id.partner_id.state_id = self.state_us_4
        self.user.company_id.partner_id.city_id = self.us_city_a
        unusual_days = self.leave_model.with_user(self.user.id).get_unusual_days(
            "2019-07-01", date_to="2019-07-31"
        )
        self.assertTrue(unusual_days["2019-07-29"])
        self.assertTrue(unusual_days["2019-07-30"])
        self.assertFalse(unusual_days["2019-07-31"])

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_state_city(
        self,
    ):
        self.address.country_id = self.us_country
        self.address.city_id = False
        self.user.company_id.partner_id.city_id = self.us_city_a
        unusual_days = self.leave_model.with_user(self.user.id).get_unusual_days(
            "2019-07-01", date_to="2019-07-31"
        )
        self.assertFalse(unusual_days["2019-07-29"])
        self.assertFalse(unusual_days["2019-07-30"])
        self.assertFalse(unusual_days["2019-07-31"])
