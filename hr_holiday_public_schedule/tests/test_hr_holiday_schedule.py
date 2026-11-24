# Copyright 2026 Daniel Reis <dreis.pt@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import date

from odoo.tests.common import TransactionCase


class TestHrHolidaySchedule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.country = cls.env.ref("base.pt")
        cls.company.partner_id.country_id = cls.country
        cls.company.resource_calendar_id.tz = "UTC"
        cls.Schedule = cls.env["hr.holiday.schedule"]
        cls.Rule = cls.env["hr.holiday.schedule.rule"]
        cls.Leave = cls.env["resource.calendar.leaves"]

    def _create_schedule(self, year=2026, rules=None):
        return self.Schedule.create(
            {
                "name": "Test Holiday Schedule",
                "year_to_generate": year,
                "country_ids": [(6, 0, self.country.ids)],
                "rule_ids": [(0, 0, vals) for vals in rules or []],
            }
        )

    def _leaves_for(self, schedule, year=2026):
        return self.Leave.search(
            [
                ("hr_holiday_schedule_id", "=", schedule.id),
                ("hr_holiday_year", "=", year),
            ]
        )

    def test_generate_country_wide_rules(self):
        schedule = self._create_schedule(
            rules=[
                {
                    "name": "Christmas",
                    "rule_type": "fixed",
                    "month": 12,
                    "day": 25,
                },
                {
                    "name": "Good Friday",
                    "rule_type": "easter",
                    "easter_offset": -2,
                },
                {
                    "name": "Fourth Thursday",
                    "rule_type": "nth_weekday",
                    "month": 11,
                    "weekday": "3",
                    "ordinal": "4",
                },
                {
                    "name": "Observed Saturday",
                    "rule_type": "fixed",
                    "month": 7,
                    "day": 4,
                    "observed_shift": "closest_weekday",
                },
            ]
        )
        schedule.action_generate()
        leaves = self._leaves_for(schedule)
        self.assertEqual(len(leaves), 4)
        self.assertEqual(
            {leave.date_from.date() for leave in leaves},
            {
                date(2026, 12, 25),
                date(2026, 4, 3),
                date(2026, 11, 26),
                date(2026, 7, 3),
            },
        )
        self.assertTrue(all(not leave.resource_id for leave in leaves))
        self.assertTrue(all(leave.time_type == "leave" for leave in leaves))
        self.assertTrue(all(leave.hr_holiday_year == 2026 for leave in leaves))
        self.assertTrue(all(leave.company_id == self.company for leave in leaves))

    def test_generate_is_idempotent(self):
        schedule = self._create_schedule(
            rules=[
                {
                    "name": "New Year",
                    "rule_type": "fixed",
                    "month": 1,
                    "day": 1,
                }
            ]
        )
        schedule.action_generate()
        schedule.action_generate()
        self.assertEqual(len(self._leaves_for(schedule)), 1)

    def test_delete_generated(self):
        schedule = self._create_schedule(
            rules=[
                {
                    "name": "New Year",
                    "rule_type": "fixed",
                    "month": 1,
                    "day": 1,
                }
            ]
        )
        schedule.action_generate()
        self.assertEqual(len(self._leaves_for(schedule)), 1)
        schedule.action_delete_generated()
        self.assertFalse(self._leaves_for(schedule))

    def test_scoped_rule_zip_range(self):
        address_in = self.env["res.partner"].create(
            {
                "name": "Employee In Zip",
                "country_id": self.country.id,
                "zip": "1500-001",
            }
        )
        address_out = self.env["res.partner"].create(
            {
                "name": "Employee Out Zip",
                "country_id": self.country.id,
                "zip": "2000-000",
            }
        )
        employee_in = self.env["hr.employee"].create(
            {"name": "Employee In", "address_id": address_in.id}
        )
        employee_out = self.env["hr.employee"].create(
            {"name": "Employee Out", "address_id": address_out.id}
        )
        schedule = self._create_schedule(
            rules=[
                {
                    "name": "Zip Holiday",
                    "rule_type": "fixed",
                    "month": 1,
                    "day": 1,
                    "zip_min": "1000-000",
                    "zip_max": "1999-999",
                }
            ]
        )
        schedule.action_generate()
        leaves = self._leaves_for(schedule)
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves.resource_id, employee_in.resource_id)
        self.assertNotEqual(leaves.resource_id, employee_out.resource_id)
        self.assertEqual(leaves.company_id, self.company)

    def test_archived_rule_is_skipped(self):
        schedule = self._create_schedule(
            rules=[
                {
                    "name": "New Year",
                    "rule_type": "fixed",
                    "month": 1,
                    "day": 1,
                },
                {
                    "name": "Carnival",
                    "rule_type": "fixed",
                    "month": 2,
                    "day": 17,
                    "active": False,
                },
            ]
        )
        schedule.action_generate()
        leaves = self._leaves_for(schedule)
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves.name, "New Year")
