# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.hr_holidays_public.tests import test_holidays_public


class TestHolidaysPublicBase(test_holidays_public.TestHolidaysPublic):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model_line = cls.env["calendar.public.holiday.line"]
        cls.work_location_model = cls.env["hr.work.location"]
        cls.work_location_a = cls.work_location_model.create(
            {
                "name": "Work Location A (US)",
                "address_id": cls.env.company.partner_id.id,
            }
        )
        cls.work_location_b = cls.work_location_model.create(
            {
                "name": "Work Location B (US)",
                "address_id": cls.env.company.partner_id.id,
            }
        )


class TestHolidaysPublic(TestHolidaysPublicBase):
    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, state_ids=False, work_location_ids=False
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
                "public_holiday_id": holiday.id,
                "state_ids": state_ids,
                "work_location_ids": work_location_ids,
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
        self.env.ref("base.user_demo").employee_id.work_location_id = False
        self.employee.address_id.country_id = self.env.ref("base.us")
        self.employee.address_id.state_id = self.env.ref("base.state_us_4")
        self.employee.work_location_id = self.work_location_a

        self.leave_model = self.leave_model.with_context(employee_id=self.employee.id)
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[(6, 0, [self.employee.address_id.state_id.id])],
            work_location_ids=[(6, 0, [self.employee.work_location_id.id])],
        )

    def test_get_unusual_days_return_public_holidays_same_state_same_work_location(
        self,
    ):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl = self.env.ref("base.user_demo").employee_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl.work_location_id = self.work_location_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
            work_location_ids=[(6, 0, [demo_user_empl.work_location_id.id])],
        )

    def test_get_unusual_days_return_public_holidays_same_state_different_work_location(
        self,
    ):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl = self.env.ref("base.user_demo").employee_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl.work_location_id = self.work_location_a
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
            work_location_ids=[(6, 0, [self.work_location_b.id])],
        )

    def test_get_unusual_days_return_public_holidays_no_state_same_work_location(self):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl = self.env.ref("base.user_demo").employee_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl.work_location_id = self.work_location_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            work_location_ids=[(6, 0, [demo_user_empl.work_location_id.id])],
        )

    def test_get_unusual_days_return_public_holidays_no_state_different_work_location(
        self,
    ):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl = self.env.ref("base.user_demo").employee_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        demo_user_empl.work_location_id = self.work_location_a
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            work_location_ids=[(6, 0, [demo_user_empl.work_location_id.id])],
        )
