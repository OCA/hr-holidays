# Copyright 2015 Salton Massally <smassally@idtlabs.sl>
# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 glueckkanja AG
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
        cls.region_1 = cls.env["calendar.public.holiday.region"].create(
            {"name": "Region 1"}
        )
        cls.region_2 = cls.env["calendar.public.holiday.region"].create(
            {"name": "Region 2"}
        )
        # The region of an employee follows their work location.
        cls.work_location = cls.env["hr.work.location"].create(
            {"name": "Office", "address_id": cls.res_partner.id}
        )
        # A running contract is required: since odoo/odoo@45c601bf,
        # get_unusual_days() returns True for every day outside of the
        # employee's contracts, which would make the tested dates unusual
        # regardless of the public holidays.
        cls.employee = cls.employee_model.create(
            {
                "name": "Employee 1",
                "address_id": cls.res_partner.id,
                "work_location_id": cls.work_location.id,
                "date_version": "2019-01-01",
                "contract_date_start": "2019-01-01",
            }
        )

    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, region_ids=False
    ):
        self.assertFalse(
            self.leave_model.with_context(employee_id=self.employee.id)
            .get_unusual_days("2019-07-01 00:00:00", date_to="2019-07-31 23:59:59")
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
                            "region_ids": region_ids,
                        },
                    )
                ],
            }
        )
        self.assertEqual(
            self.leave_model.with_context(
                employee_id=self.employee.id
            ).get_unusual_days("2019-07-01 00:00:00", date_to="2019-07-31 23:59:59")[
                "2019-07-30"
            ],
            expected,
        )

    def test_public_holidays_context(self):
        self.employee.address_id.country_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=False,
        )

    def test_empty_regions_show_their_placeholder(self):
        """While editing, an empty cell reads as "applies everywhere"."""
        arch = self.env.ref(
            "calendar_public_holiday.view_calendar_public_holiday_form"
        ).get_combined_arch()
        self.assertIn('placeholder="All Regions"', arch)

    def test_get_unusual_days_return_public_holidays_same_country(self):
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.employee.address_id.country_id.id,
        )

    def test_get_unusual_days_return_general_public_holidays(self):
        self.assertPublicHolidayIsUnusualDay(True, country_id=False)

    def test_get_unusual_days_not_return_public_holidays_different_country(self):
        self.employee.address_id.country_id = self.country_2.id
        self.assertPublicHolidayIsUnusualDay(False, country_id=self.country_1.id)

    def test_get_unusual_days_return_public_holidays_fallback_to_company_country(self):
        self.employee.address_id.country_id = False
        self.assertPublicHolidayIsUnusualDay(
            True, country_id=self.env.company.country_id.id
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_country(
        self,
    ):
        self.employee.address_id.country_id = False
        self.env.company.country_id = self.country_2.id
        self.assertPublicHolidayIsUnusualDay(False, country_id=self.country_1.id)

    def test_get_unusual_days_return_public_holidays_same_region(self):
        self.work_location.public_holiday_region_id = self.region_1
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.employee.address_id.country_id.id,
            region_ids=[(6, 0, self.region_1.ids)],
        )

    def test_get_unusual_days_not_return_public_holidays_different_region(self):
        self.work_location.public_holiday_region_id = self.region_1
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.country_1.id,
            region_ids=[(6, 0, self.region_2.ids)],
        )

    def test_get_unusual_days_not_return_regional_public_holidays_without_region(
        self,
    ):
        self.assertFalse(self.employee.public_holiday_region_id)
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.country_1.id,
            region_ids=[(6, 0, self.region_1.ids)],
        )

    def test_the_region_country_wins_over_the_work_address(self):
        """A region of another country hides this country's calendars."""
        self.assertEqual(self.employee.address_id.country_id, self.country_1)
        self.region_1.country_id = self.country_2
        self.work_location.public_holiday_region_id = self.region_1
        self.assertPublicHolidayIsUnusualDay(False, country_id=self.country_1.id)

    def test_the_region_country_selects_its_own_calendars(self):
        self.region_1.country_id = self.country_2
        self.work_location.public_holiday_region_id = self.region_1
        self.assertPublicHolidayIsUnusualDay(True, country_id=self.country_2.id)

    def test_region_follows_the_work_location(self):
        self.work_location.public_holiday_region_id = self.region_1
        self.assertEqual(self.employee.public_holiday_region_id, self.region_1)
        self.employee.work_location_id = self.env["hr.work.location"].create(
            {
                "name": "Elsewhere",
                "address_id": self.res_partner.id,
                "public_holiday_region_id": self.region_2.id,
            }
        )
        self.assertEqual(self.employee.public_holiday_region_id, self.region_2)

    def test_is_public_holiday_honours_the_region(self):
        # holiday_1 is the 2024 calendar of the employee's country.
        self.holiday_line_model.create(
            {
                "name": "Regional",
                "date": "2024-12-26",
                "public_holiday_id": self.holiday_1.id,
                "region_ids": [(6, 0, self.region_1.ids)],
            }
        )
        with freeze_time("2024-12-26"):
            self.employee.invalidate_recordset(["is_public_holiday"])
            self.assertFalse(self.employee.is_public_holiday)
            self.work_location.public_holiday_region_id = self.region_1
            self.employee.invalidate_recordset(["is_public_holiday"])
            self.assertTrue(self.employee.is_public_holiday)

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
