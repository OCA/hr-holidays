# Copyright 2015 Salton Massally <smassally@idtlabs.sl>
# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestHolidaysPublic(TransactionCase):
    at_install = False
    post_install = True

    def setUp(self):
        super(TestHolidaysPublic, self).setUp()
        self.holiday_model = self.env["hr.holidays.public"]
        self.holiday_model_line = self.env["hr.holidays.public.line"]
        self.employee_model = self.env["hr.employee"]
        self.wizard_next_year = self.env["public.holidays.next.year.wizard"]

        # Remove possibly existing public holidays that would interfer.
        self.holiday_model_line.search([]).unlink()
        self.holiday_model.search([]).unlink()

        # Create holidays
        holiday2 = self.holiday_model.create(
            {"year": 1994, "country_id": self.env.ref("base.sl").id}
        )
        self.holiday_model_line.create(
            {"name": "holiday 5", "date": "1994-10-14", "year_id": holiday2.id}
        )

        holiday3 = self.holiday_model.create(
            {"year": 1994, "country_id": self.env.ref("base.sk").id}
        )
        self.holiday_model_line.create(
            {"name": "holiday 6", "date": "1994-11-14", "year_id": holiday3.id}
        )

        self.holiday1 = self.holiday_model.create({"year": 1995})
        for dt in ["1995-10-14", "1995-12-31", "1995-01-01"]:
            self.holiday_model_line.create(
                {"name": "holiday x", "date": dt, "year_id": self.holiday1.id}
            )

        self.employee = self.employee_model.create(
            {
                "name": "Employee 1",
                "address_id": self.env["res.partner"]
                .create(
                    {"name": "Employee 1", "country_id": self.env.ref("base.sl").id}
                )
                .id,
            }
        )

    def test_name_get(self):
        hol = self.holiday_model.create({"year": 1999})
        hol_name = hol.name_get()[0]
        self.assertEqual(hol_name, (hol.id, str(hol.year)))

    def test_duplicate_year_country_fail(self):
        # ensures that duplicate year cannot be created for the same country
        with self.assertRaises(ValidationError):
            self.holiday_model.create({"year": 1995})
        with self.assertRaises(ValidationError):
            self.holiday_model.create(
                {"year": 1994, "country_id": self.env.ref("base.sl").id}
            )

    def test_duplicate_date_state_fail(self):
        # ensures that duplicate date cannot be created for the same country
        # state or with state null
        holiday4 = self.holiday_model.create(
            {"year": 1994, "country_id": self.env.ref("base.us").id}
        )
        hline = self.holiday_model_line.create(
            {"name": "holiday x", "date": "1994-11-14", "year_id": holiday4.id}
        )
        with self.assertRaises(ValidationError):
            self.holiday_model_line.create(
                {"name": "holiday x", "date": "1994-11-14", "year_id": holiday4.id}
            )
        hline.state_ids = [(6, 0, [self.env.ref("base.state_us_35").id])]
        with self.assertRaises(ValidationError):
            self.holiday_model_line.create(
                {
                    "name": "holiday x",
                    "date": "1994-11-14",
                    "year_id": holiday4.id,
                    "state_ids": [(6, 0, [self.env.ref("base.state_us_35").id])],
                }
            )

    def test_isnot_holiday(self):
        # ensures that if given a date that is not an holiday it returns none
        self.assertFalse(self.holiday_model.is_public_holiday(date(1995, 12, 10)))

    def test_is_holiday(self):
        # ensures that correct holidays are identified
        self.assertTrue(self.holiday_model.is_public_holiday(date(1995, 10, 14)))

    def test_isnot_holiday_in_country(self):
        # ensures that correct holidays are identified for a country
        self.assertFalse(
            self.holiday_model.is_public_holiday(
                date(1994, 11, 14), employee_id=self.employee.id
            )
        )

    def test_is_holiday_in_country(self):
        # ensures that correct holidays are identified for a country
        self.assertTrue(
            self.holiday_model.is_public_holiday(
                date(1994, 10, 14), employee_id=self.employee.id
            )
        )

    def test_holiday_line_year(self):
        # ensures that line year and holiday year are the same
        holiday4 = self.holiday_model.create({"year": 1994})
        with self.assertRaises(ValidationError):
            self.holiday_model_line.create(
                {"name": "holiday x", "date": "1995-11-14", "year_id": holiday4.id}
            )

    def test_list_holidays_in_list_country_specific(self):
        # ensures that correct holidays are identified for a country
        lines = self.holiday_model.get_holidays_list(1994, employee_id=self.employee.id)
        res = lines.filtered(lambda r: r.date == date(1994, 10, 14))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 1)

    def test_list_holidays_in_list(self):
        # ensures that correct holidays are identified for a country
        lines = self.holiday_model.get_holidays_list(1995)
        res = lines.filtered(lambda r: r.date == date(1995, 10, 14))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 3)

    def test_create_next_year_public_holidays(self):
        old_meeting = self.holiday1.line_ids[0].meeting_id
        self.wizard_next_year.new().create_public_holidays()
        # Ensure that the previous meeting date is preserved
        self.assertEqual(old_meeting.start.year, 1995)
        lines = self.holiday_model.get_holidays_list(1996)
        # The meeting is not the same for the new entries
        self.assertFalse(any(x.meeting_id == old_meeting for x in lines))
        # There's a meeting for the new entries
        self.assertTrue(lines[0].meeting_id)
        self.assertEqual(lines[0].meeting_id.start.year, 1996)
        res = lines.filtered(lambda r: r.date == date(1996, 10, 14))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 3)

    def test_create_year_2000_public_holidays(self):
        ph_start_ids = self.holiday_model.search([("year", "=", 1994)])
        val = {"template_ids": ph_start_ids, "year": 2000}
        wz_create_ph = self.wizard_next_year.new(values=val)

        wz_create_ph.create_public_holidays()

        lines = self.holiday_model.get_holidays_list(2000)
        self.assertEqual(len(lines), 2)

        res = lines.filtered(
            lambda r: r.year_id.country_id.id == self.env.ref("base.sl").id
        )
        self.assertEqual(len(res), 1)

    def test_february_29th(self):
        # Ensures that users get a UserError (not a nasty Exception) when
        # trying to create public holidays from year including 29th of
        # February
        holiday_tw_2016 = self.holiday_model.create(
            {"year": 2016, "country_id": self.env.ref("base.tw").id}
        )

        self.holiday_model_line.create(
            {
                "name": "Peace Memorial Holiday",
                "date": "2016-02-29",
                "year_id": holiday_tw_2016.id,
            }
        )

        val = {"template_ids": holiday_tw_2016}
        wz_create_ph = self.wizard_next_year.new(values=val)

        with self.assertRaises(UserError):
            wz_create_ph.create_public_holidays()

    def test_calendar_event_created(self):
        holiday = self.holiday_model.create(
            {"year": 2019, "country_id": self.env.ref("base.us").id}
        )
        hline = self.holiday_model_line.create(
            {"name": "holiday x", "date": "2019-07-30", "year_id": holiday.id}
        )
        meeting_id = hline.meeting_id
        self.assertTrue(meeting_id)
        hline.unlink()
        self.assertFalse(meeting_id.exists())

    def assertPublicHolidayIsUnusualDay(
        self, expected, country_id=None, state_ids=False
    ):
        self.assertFalse(
            self.env["hr.leave"]
            .with_user(self.env.ref("base.user_demo").id)
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
            }
        )
        self.assertEqual(
            self.env["hr.leave"]
            .with_user(self.env.ref("base.user_demo").id)
            .get_unusual_days("2019-07-01", date_to="2019-07-31")["2019-07-30"],
            expected,
        )

    def test_get_unusual_days_return_public_holidays_same_country(self):
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.company.state_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
        )

    def test_get_unusual_days_return_general_public_holidays(self):
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.company.state_id = False
        self.assertPublicHolidayIsUnusualDay(True, country_id=False)

    def test_get_unusual_days_not_return_public_holidays_different_country(self):
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.company.state_id = False
        self.env.ref("base.user_demo").employee_id.address_id.country_id = self.env.ref(
            "base.fr"
        )
        self.assertPublicHolidayIsUnusualDay(
            False, country_id=self.env.ref("base.us").id
        )

    def test_get_unusual_days_return_public_holidays_fallback_to_company_country(self):
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.company.state_id = False
        self.env.ref("base.user_demo").employee_id.address_id.country_id = False
        self.assertPublicHolidayIsUnusualDay(
            True, country_id=self.env.company.country_id.id
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_country(
        self,
    ):
        self.env.ref("base.user_demo").employee_id.address_id.state_id = False
        self.env.company.state_id = False
        self.env.ref("base.user_demo").employee_id.address_id.country_id = False
        self.env.company.country_id = self.env.ref("base.fr")
        self.assertPublicHolidayIsUnusualDay(
            False, country_id=self.env.ref("base.us").id
        )

    def test_get_unusual_days_return_public_holidays_same_state(self):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.ref(
                "base.user_demo"
            ).employee_id.address_id.country_id.id,
            state_ids=[(6, 0, [demo_user_empl_addr.state_id.id])],
        )

    def test_get_unusual_days_not_return_public_holidays_different_state(self):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = self.env.ref("base.state_us_4")
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=self.env.ref("base.us").id,
            state_ids=[(6, 0, [self.env.ref("base.state_us_35").id])],
        )

    def test_get_unusual_days_return_public_holidays_fallback_to_company_state(self):
        self.env.ref("base.user_demo").employee_id = False
        self.assertPublicHolidayIsUnusualDay(
            True,
            country_id=self.env.company.country_id.id,
            state_ids=[(6, 0, [self.env.company.state_id.id])],
        )

    def test_get_unusual_days_not_return_public_holidays_fallback_to_company_state(
        self,
    ):
        demo_user_empl_addr = self.env.ref("base.user_demo").employee_id.address_id
        demo_user_empl_addr.country_id = self.env.ref("base.us")
        demo_user_empl_addr.state_id = False
        self.env.company.state_id = self.env.ref("base.state_us_4")
        self.assertPublicHolidayIsUnusualDay(
            False,
            country_id=demo_user_empl_addr.country_id.id,
            state_ids=[(6, 0, [self.env.ref("base.state_us_3").id])],
        )
