# Copyright 2023-2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.hr_holidays_public.tests import test_holidays_calculation


class TestHolidaysComputeDays(test_holidays_calculation.TestHolidaysComputeDays):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.es_city_a = cls.env["res.city"].create(
            {
                "name": "Test city A",
                "state_id": cls.env.ref("base.state_es_cr").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.address_2.city_id = cls.es_city_a
        cls.public_holiday_country.line_ids.city_ids = cls.address_2.city_id.ids

    # Run all tests of hr_holidays_public


class TestHolidaysComputeDaysExtra(test_holidays_calculation.TestHolidaysComputeDays):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.es_city_a = cls.env["res.city"].create(
            {
                "name": "Test city A",
                "state_id": cls.env.ref("base.state_es_cr").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.es_city_b = cls.env["res.city"].create(
            {
                "name": "Test city B",
                "state_id": cls.env.ref("base.state_es_cr").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.address_2.city_id = cls.es_city_b
        cls.public_holiday_country.line_ids.city_ids = cls.es_city_a.ids

    def test_number_days_excluding_employee_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 4)

    def test_number_days_across_year_2(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1947-01-03 23:59:59",  # Friday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 7)

    def test_number_of_hours_excluding_employee_2(self):
        self.holiday_type.request_unit = "hour"
        leave_request = self.HrLeave.new(
            {
                "date_from": "1946-12-23 00:00:00",  # Monday
                "date_to": "1946-12-29 23:59:59",  # Sunday
                "holiday_status_id": self.holiday_type.id,
                "employee_id": self.employee_2.id,
            }
        )
        self.assertEqual(leave_request.number_of_days, 4)
