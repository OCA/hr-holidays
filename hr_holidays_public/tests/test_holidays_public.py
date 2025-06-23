# Copyright 2015 Salton Massally <smassally@idtlabs.sl>
# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

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
        cls.employee = cls.employee_model.create(
            {
                "name": "Employee 1",
                "address_id": cls.res_partner.id,
            }
        )

    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, state_ids=False
    ):
        self.assertFalse(
            self.leave_model.with_context(employee_id=self.employee.id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")
            .get("2019-07-30", False)
        )
        self.holiday_model.create(
            {
                "year": 2019,
                "country_id": country_id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "holiday x",
                            "date": "2019-07-30",
                            "state_ids": state_ids,
                        },
                    )
                ],
            }
        )
        self.assertEqual(
            self.leave_model.with_context(
                employee_id=self.employee.id
            ).get_unusual_days("2019-07-01", date_to="2019-07-31")["2019-07-30"],
            expected,
        )

    def test_public_holidays_context(self):
        self.employee.address_id.country_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=False,
        )

    def test_get_unusual_days_return_public_holidays_same_country(self):
        self.employee.address_id.state_id = False
        self.env.company.state_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.employee.address_id.country_id.id,
        )

    def test_get_unusual_days_return_general_public_holidays(self):
        self.employee.address_id.state_id = False
        self.env.company.state_id = False
        self.assertPublicHolidayIsUnusualDay(True, country_id=False)

    def test_get_unusual_days_not_return_public_holidays_different_country(self):
        self.employee.address_id.state_id = False
        self.env.company.state_id = False
        self.employee.address_id.country_id = self.country_2.id
        self.assertPublicHolidayIsUnusualDay(False, country_id=self.country_1.id)

    def test_get_unusual_days_return_public_holidays_fallback_to_company_country(self):
        self.employee.address_id.state_id = False
        self.env.company.state_id = False
        self.employee.address_id.country_id = False
        self.assertPublicHolidayIsUnusualDay(
            True, country_id=self.env.company.country_id.id
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_country(
        self,
    ):
        self.employee.address_id.state_id = False
        self.env.company.state_id = False
        self.employee.address_id.country_id = False
        self.env.company.country_id = self.country_2.id
        self.assertPublicHolidayIsUnusualDay(False, country_id=self.country_1.id)

    def test_get_unusual_days_return_public_holidays_same_state(self):
        self.employee.address_id.country_id = self.country_1.id
        self.employee.address_id.state_id = self.st_state_1.id
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.employee.address_id.country_id.id,
            state_ids=[(6, 0, [self.employee.address_id.state_id.id])],
        )

    def test_get_unusual_days_not_return_public_holidays_different_state(self):
        self.employee.address_id.state_id = self.st_state_1.id
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.country_1.id,
            state_ids=[(6, 0, [self.st_state_2.id])],
        )

    def test_get_unusual_days_return_public_holidays_fallback_to_company_state(self):
        self.employee.address_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.company.country_id.id,
            state_ids=[(6, 0, [self.env.company.state_id.id])],
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_state(
        self,
    ):
        self.employee.address_id.country_id = self.country_1.id
        self.employee.address_id.state_id = False
        self.env.company.state_id = self.st_state_2
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.employee.address_id.country_id.id,
            state_ids=[(6, 0, [self.st_state_1.id])],
        )

    @freeze_time("2024-12-25")
    def test_user_im_status(self):
        self.assertTrue(self.employee.is_public_holiday)
        self.assertEqual(self.employee.hr_icon_display, "presence_holiday_absent")
        self.assertTrue(self.employee.is_absent)
        user = new_test_user(self.env, login="test-user")
        self.assertEqual(user.im_status, "offline")
        self.assertEqual(user.partner_id.im_status, "offline")
        self.employee.user_id = user
        user.invalidate_recordset()
        self.assertEqual(user.im_status, "leave_offline")
        user.partner_id.invalidate_recordset()
        self.assertEqual(user.partner_id.im_status, "leave_offline")
