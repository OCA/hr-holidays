# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from freezegun import freeze_time

from odoo.exceptions import UserError, ValidationError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestHolidaysPublicRegionalBase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model = cls.env["hr.holidays.public.regional"]
        cls.holiday_model_line = cls.env["hr.holidays.public.regional.line"]
        cls.employee_model = cls.env["hr.employee"]
        cls.wizard_next_year = cls.env["public.regional.holidays.wizard"]
        cls.leave_model = cls.env["hr.leave"]

        # Create holidays
        holiday2 = cls.holiday_model.create({"name": "Holiday 2", "year": 1994})
        cls.holiday_model_line.create(
            {"name": "holiday 5", "date": "1994-10-14", "calendar_id": holiday2.id}
        )

        holiday3 = cls.holiday_model.create({"name": "Holiday 3", "year": 1994})
        cls.holiday_model_line.create(
            {"name": "holiday 6", "date": "1994-11-14", "calendar_id": holiday3.id}
        )

        cls.holiday1 = cls.holiday_model.create({"name": "Holiday 1", "year": 1995})
        for dt in ["1995-10-14", "1995-12-31", "1995-01-01"]:
            cls.holiday_model_line.create(
                {"name": "holiday x", "date": dt, "calendar_id": cls.holiday1.id}
            )

        cls.employee = cls.employee_model.create({"name": "Test Employee"})
        cls.env["hr.employee.regional.calendar"].create(
            {
                "employee_id": cls.employee.id,
                "calendar_id": holiday2.id,
                "start_date": "1994-01-01",
                "end_date": "1994-12-31",
            }
        )


class TestHolidaysPublicRegional(TestHolidaysPublicRegionalBase):
    def test_duplicate_date_state_fail(self):
        holiday4 = self.holiday_model.create({"name": "Holiday 4", "year": 1994})
        self.holiday_model_line.create(
            {"name": "holiday x", "date": "1994-11-14", "calendar_id": holiday4.id}
        )
        with self.assertRaises(ValidationError):
            self.holiday_model_line.create(
                {"name": "holiday x", "date": "1994-11-14", "calendar_id": holiday4.id}
            )

    def test_isnot_holiday(self):
        self.assertFalse(
            self.holiday_model.is_public_regional_holiday(
                date(1995, 12, 10), self.employee
            )
        )

    def test_is_holiday(self):
        self.assertTrue(
            self.holiday_model.is_public_regional_holiday(
                date(1994, 10, 14), self.employee
            )
        )

    def test_holiday_line_year(self):
        holiday4 = self.holiday_model.create({"name": "Holiday 4", "year": 1994})
        with self.assertRaises(ValidationError):
            self.holiday_model_line.create(
                {"name": "holiday x", "date": "1995-11-14", "calendar_id": holiday4.id}
            )

    def test_list_holidays_in_list(self):
        lines = self.holiday_model.get_regional_holidays_list(
            employee=self.employee, year=1994
        )
        res = lines.filtered(lambda r: r.date == date(1994, 10, 14))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 1)

    def test_create_year_2000_public_holidays(self):
        ph_start_ids = self.holiday_model.search([("year", "=", 1994)])
        val = {"template_ids": ph_start_ids, "year": 2000}
        wz_create_ph = self.wizard_next_year.new(values=val)

        wz_create_ph.create_public_regional_holidays()

        lines = self.holiday_model_line.search([("calendar_id.year", "=", 2000)])
        self.assertEqual(len(lines), 2)

    def test_february_29th(self):
        holiday_tw_2016 = self.holiday_model.create(
            {"name": "Holiday TW 2016", "year": 2016}
        )

        self.holiday_model_line.create(
            {
                "name": "Peace Memorial Holiday",
                "date": "2016-02-29",
                "calendar_id": holiday_tw_2016.id,
            }
        )

        val = {"template_ids": holiday_tw_2016}
        wz_create_ph = self.wizard_next_year.new(values=val)

        with self.assertRaises(UserError):
            wz_create_ph.create_public_regional_holidays()

    def test_calendar_event_created(self):
        holiday = self.holiday_model.create({"name": "Holiday 2019", "year": 2019})
        hline = self.holiday_model_line.create(
            {"name": "holiday x", "date": "2019-07-30", "calendar_id": holiday.id}
        )
        meeting_id = hline.meeting_id
        self.assertTrue(meeting_id)
        hline.unlink()
        self.assertFalse(meeting_id.exists())

    def assertPublicHolidayIsUnusualDay(self, expected):
        self.assertFalse(
            self.leave_model.with_user(self.env.ref("base.user_demo").id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")
            .get("2019-07-30", False)
        )
        holiday = self.holiday_model.create({"year": 2019})
        self.holiday_model_line.create(
            {
                "name": "holiday x",
                "date": "2019-07-30",
                "calendar_id": holiday.id,
            }
        )
        self.env["hr.employee.regional.calendar"].create(
            {
                "employee_id": self.employee.id,
                "calendar_id": holiday.id,
                "start_date": "2019-01-01",
                "end_date": "2019-12-31",
            }
        )
        self.assertEqual(
            self.leave_model.with_user(
                self.env.ref("base.user_demo").id
            ).get_unusual_days("2019-07-01", date_to="2019-07-31")["2019-07-30"],
            expected,
        )

    def test_public_holidays_context(self):
        self.leave_model = self.leave_model.with_context(employee_id=self.employee.id)
        self.assertFalse(
            self.leave_model.with_user(self.env.ref("base.user_demo").id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")
            .get("2019-07-30", False)
        )
        holiday = self.holiday_model.create({"name": "Holiday 2019", "year": 2019})
        self.holiday_model_line.create(
            {
                "name": "holiday x",
                "date": "2019-07-30",
                "calendar_id": holiday.id,
            }
        )
        self.env["hr.employee.regional.calendar"].create(
            {
                "employee_id": self.employee.id,
                "calendar_id": holiday.id,
                "start_date": "2019-01-01",
                "end_date": "2019-12-31",
            }
        )
        self.assertTrue(
            self.leave_model.with_user(
                self.env.ref("base.user_demo").id
            ).get_unusual_days("2019-07-01", date_to="2019-07-31")["2019-07-30"],
        )

    @freeze_time("1994-10-14")
    def test_user_im_status(self):
        self.assertTrue(self.employee.is_public_regional_holiday)
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
