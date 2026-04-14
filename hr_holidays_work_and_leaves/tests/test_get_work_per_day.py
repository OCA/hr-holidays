# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime

from .common import WorkAndLeavesBase


class TestGetWorkPerDay(WorkAndLeavesBase):
    def test_five_work_days_wednesday_to_tuesday(self):
        """_get_work_per_day yields exactly 5 entries for Wed–Tue spanning a weekend."""
        # Wednesday 2026-05-20 07:00 UTC — before work starts
        start_datetime = datetime(2026, 5, 20, 7, 0, 0)
        # Tuesday 2026-05-26 18:00 UTC — after work ends
        end_datetime = datetime(2026, 5, 26, 18, 0, 0)

        work_days = list(self.employee._get_work_per_day(start_datetime, end_datetime))

        self.assertEqual(len(work_days), 5)
        expected_dates = [
            date(2026, 5, 20),  # Wednesday
            date(2026, 5, 21),  # Thursday
            date(2026, 5, 22),  # Friday
            date(2026, 5, 25),  # Monday (Saturday and Sunday skipped)
            date(2026, 5, 26),  # Tuesday
        ]
        actual_dates = [entry.datetime_from.date() for entry in work_days]
        self.assertEqual(actual_dates, expected_dates)
        for entry in work_days:
            self.assertEqual(entry.duration, 8.0)
            self.assertEqual(entry.type, "work")

    def test_nine_work_days_two_week_period(self):
        """Two-week calendar yields 9 entries: 5 in even week, 4 in odd week (Mon off)."""
        # Monday 2026-05-11 is ISO week 20 (even → week_type 0): all 5 days work.
        # Monday 2026-05-18 is ISO week 21 (odd  → week_type 1): Mon off, 4 days work.
        start_datetime = datetime(2026, 5, 11, 7, 0, 0)
        end_datetime = datetime(2026, 5, 22, 18, 0, 0)

        work_days = list(
            self.employee_two_week._get_work_per_day(start_datetime, end_datetime)
        )

        self.assertEqual(len(work_days), 9)
        expected_dates = [
            date(2026, 5, 11),  # Monday   — even week
            date(2026, 5, 12),  # Tuesday  — even week
            date(2026, 5, 13),  # Wednesday — even week
            date(2026, 5, 14),  # Thursday — even week
            date(2026, 5, 15),  # Friday   — even week
            # May 18 (Monday) skipped — odd week has no Monday
            date(2026, 5, 19),  # Tuesday  — odd week
            date(2026, 5, 20),  # Wednesday — odd week
            date(2026, 5, 21),  # Thursday — odd week
            date(2026, 5, 22),  # Friday   — odd week
        ]
        actual_dates = [entry.datetime_from.date() for entry in work_days]
        self.assertEqual(actual_dates, expected_dates)
