from datetime import datetime

import pytz

from odoo.tests.common import TransactionCase


class TestResourceCalendar(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.calendar_flex_with_weekend = cls.env["resource.calendar"].create(
            {
                "name": "Flexible Calendar (std implementation)",
                "hours_per_day": 8.0,
                "hours_per_week": 40.0,
                "flexible_hours": True,
                "exclude_weekends": False,
                "tz": "UTC",
            }
        )
        cls.calendar_flex_without_weekend = cls.env["resource.calendar"].create(
            {
                "name": "Flexible Calendar (exclude weekends)",
                "hours_per_day": 8.0,
                "hours_per_week": 40.0,
                "flexible_hours": True,
                "exclude_weekends": True,
                "tz": "UTC",
            }
        )
        cls.UTC = pytz.timezone("UTC")
        cls.tz_FR = pytz.timezone("Europe/Paris")

    def _check(self, calendar, start_dt, end_dt, expected_duration, message):
        result_per_resource_id = calendar._attendance_intervals_batch(start_dt, end_dt)

        actual_duration = 0
        for _res_id, intervals in result_per_resource_id.items():
            for start, end, _ in intervals:
                actual_duration += (end - start).seconds
        self.assertEqual(
            actual_duration / 3600,
            expected_duration,
            message,
        )

    def test_flexible_calendar_without_weekend_starting_sat(self):
        calendar = self.calendar_flex_without_weekend
        # start on saturday
        start_dt = datetime(2025, 11, 1, 0, 0, 0).astimezone(self.UTC)
        # end on friday midnight
        end_dt = datetime(2025, 11, 8, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            calendar.full_time_required_hours,
            "for 7d starting on saturday: you get a full week duration",
        )

    def test_flexible_calendar_without_weekend_starting_mon(self):
        calendar = self.calendar_flex_without_weekend
        # start on saturday
        start_dt = datetime(2025, 11, 3, 0, 0, 0).astimezone(self.UTC)
        # end on friday midnight
        end_dt = datetime(2025, 11, 10, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            calendar.full_time_required_hours,
            "for 7d starting on monday: you get a full week duration",
        )

    def test_flexible_calendar_with_weekend_interval_duration(self):
        calendar = self.calendar_flex_with_weekend
        start_dt = datetime(2025, 11, 1, 0, 0, 0).astimezone(self.UTC)
        end_dt = datetime(2025, 11, 8, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            40,
            "std behavior: for 7 days, you get full week duration",
        )

    def test_flexible_calendar_with_weekdend_friday_to_friday(self):
        calendar = self.calendar_flex_with_weekend
        # Friday (inc.) to Friday (excl.)
        start_dt = datetime(2025, 11, 7, 0, 0, 0).astimezone(self.UTC)
        end_dt = datetime(2025, 11, 14, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            40,
            "std behavior: for 7 days, you get full week duration",
        )

    def test_flexible_calendar_end_before_start_returns_empty(self):
        calendar = self.calendar_flex_without_weekend
        start_dt = datetime(2025, 11, 10, 0, 0, 0, tzinfo=self.UTC)
        end_dt = datetime(2025, 11, 9, 0, 0, 0, tzinfo=self.UTC)

        result_per_resource_id = calendar._attendance_intervals_batch(start_dt, end_dt)

        self.assertEqual(len(result_per_resource_id), 1)
        self.assertEqual(list(result_per_resource_id[False]), [])

    def test_flexible_calendar_without_weekend_friday_sunday(self):
        calendar = self.calendar_flex_without_weekend
        start_dt = datetime(2025, 10, 31, 0, 0, 0).astimezone(self.UTC)
        end_dt = datetime(2025, 11, 3, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            8,
            "For a full day, the interval must match full time required hours",
        )

    def test_flexible_calendar_without_weekend_2w_starting_wed(self):
        calendar = self.calendar_flex_without_weekend
        # start on saturday
        start_dt = datetime(2025, 11, 5, 0, 0, 0).astimezone(self.UTC)
        # end on friday midnight
        end_dt = datetime(2025, 11, 19, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            calendar.full_time_required_hours * 2,
            "for 2w starting on wed: you get 2 full weeks duration",
        )

    def test_flexible_calendar_without_weekend_10d_starting_mon(self):
        calendar = self.calendar_flex_without_weekend
        # start on saturday
        start_dt = datetime(2025, 11, 3, 0, 0, 0).astimezone(self.UTC)
        # end on friday midnight
        end_dt = datetime(2025, 11, 13, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            8 * 8,
            "for 10d starting on Mon: you get 8d",
        )

    def test_flexible_calendar_without_weekend_10d_starting_fri(self):
        calendar = self.calendar_flex_without_weekend
        # start on saturday
        start_dt = datetime(2025, 11, 7, 0, 0, 0).astimezone(self.UTC)
        # end on friday midnight
        end_dt = datetime(2025, 11, 17, 0, 0, 0).astimezone(self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            6 * 8,
            "for 10d starting on Fri: you get 6d",
        )

    def test_flexible_calendar_non_utc_1d(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # start on Mon 00:00
        start_dt = datetime(2025, 11, 2, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        # end on Tue 00:00
        end_dt = datetime(2025, 11, 3, 23, 0, 0, tzinfo=self.UTC).astimezone(self.tz_FR)
        self._check(
            calendar,
            start_dt,
            end_dt,
            1 * 8,
            "for 1d starting on Mon: you get 1d",
        )

    def test_flexible_calendar_non_utc_10d_starting_fri(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # start on Fri 00:00
        start_dt = datetime(2025, 11, 6, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        # end on Mon 00:00
        end_dt = datetime(2025, 11, 16, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        self._check(
            calendar,
            start_dt,
            end_dt,
            6 * 8,
            "for 10d starting on Fri: you get 6d",
        )

    def test_flexible_calendar_non_utc_full_week_no_offset_leak(self):
        """Regression test for a bug where a positive-offset timezone leaked
        a bogus extra day into the following week.

        Callers such as ``hr.employee._get_employees_working_hours`` build
        their date range as a UTC midnight-to-midnight week (00:00:00 to the
        following Sunday 23:59:59.999999 UTC). Converted to a timezone with a
        positive UTC offset (Europe/Zurich is UTC+2 in August), that instant
        lands a few hours past local midnight on the *following* Monday. The
        per-week chunking loop used to compare its own locally-aligned week
        boundary against that instant with exact equality, which could never
        match, so it ran one bogus extra iteration that opened a new week
        with a fresh weekly-hours budget for those few leftover hours -
        crediting up to a full UTC-offset worth of extra hours on top of the
        real weekly total (e.g. a real-world case: 40.25h computed instead
        of the correct 38.25h/week, for a 90% Planair CH contract).
        """
        calendar = self.calendar_flex_without_weekend
        calendar.tz = "Europe/Zurich"  # UTC+2 in August (CEST)
        # A full UTC calendar week, Monday 00:00:00 to the following Sunday
        # 23:59:59.999999, exactly as hr.employee._get_employees_working_hours
        # builds its bounds.
        start_dt = datetime(2026, 8, 17, 0, 0, 0, tzinfo=self.UTC)
        end_dt = datetime(2026, 8, 23, 23, 59, 59, 999999, tzinfo=self.UTC)
        self._check(
            calendar,
            start_dt,
            end_dt,
            40,  # 5 * 8h/day = hours_per_week, not 40 + a leaked UTC offset
            "for a clean UTC week converted to a positive-offset timezone, "
            "you must not get more than hours_per_week",
        )

    def test_hr_holidays_use(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        start_dt = datetime(2026, 3, 19, 0, 0, 0, tzinfo=self.UTC)
        # end on Mon 00:00
        end_dt = datetime(2026, 4, 30, 23, 59, 59, tzinfo=self.UTC)
        result_per_resource_id = calendar._attendance_intervals_batch(start_dt, end_dt)
        for _resource, intervals in result_per_resource_id.items():
            for start, end, meta in intervals:
                self.assertEqual(
                    len(meta), 1, f"more than one attendance for {start}->{end}: {meta}"
                )

    def test_get_unusual_days_excluding_weekends(self):
        calendar = self.calendar_flex_without_weekend
        start_dt = datetime(2025, 11, 3, 0, 0, 0, tzinfo=self.UTC)
        end_dt = datetime(2025, 11, 9, 0, 0, 0, tzinfo=self.UTC)

        unusual_days = calendar._get_unusual_days(start_dt, end_dt)

        self.assertFalse(unusual_days["2025-11-03"])
        self.assertFalse(unusual_days["2025-11-04"])
        self.assertFalse(unusual_days["2025-11-05"])
        self.assertFalse(unusual_days["2025-11-06"])
        self.assertFalse(unusual_days["2025-11-07"])
        self.assertTrue(unusual_days["2025-11-08"])
        self.assertTrue(unusual_days["2025-11-09"])

    def test_daylight_saving_time_1(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # week end of winter -> summer time
        start_dt = datetime(
            2026,
            3,
            27,
            23,
            0,
            0,
        ).astimezone(self.tz_FR)
        end_dt = datetime(
            2026,
            3,
            29,
            22,
            0,
            0,
        ).astimezone(self.tz_FR)
        self._check(
            calendar,
            start_dt,
            end_dt,
            0 * 8,
            "for 2d during the CET -> CEST week end, you get 0d",
        )

    def test_daylight_saving_time_2(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # week end of winter -> summer time
        start_dt = datetime(2026, 3, 26, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        end_dt = datetime(2026, 3, 29, 22, 0, 0, tzinfo=self.UTC).astimezone(self.tz_FR)
        self._check(
            calendar,
            start_dt,
            end_dt,
            1 * 8,
            "for 3d during the CET -> CEST week end, starting on Fri, you get 1d",
        )

    def test_daylight_saving_time_3(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # week end of winter -> summer time
        start_dt = datetime(2026, 3, 22, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        end_dt = datetime(2026, 3, 29, 22, 0, 0, tzinfo=self.UTC).astimezone(self.tz_FR)
        self._check(
            calendar,
            start_dt,
            end_dt,
            5 * 8,
            "for 1w including the CET -> CEST week end, starting on Mon, you get 5d",
        )

    def test_daylight_saving_time_4(self):
        calendar = self.calendar_flex_without_weekend
        calendar.tz = self.tz_FR.zone
        # week end of winter -> summer time, Fri -> Mon
        start_dt = datetime(2026, 3, 26, 23, 0, 0, tzinfo=self.UTC).astimezone(
            self.tz_FR
        )
        end_dt = datetime(2026, 3, 30, 22, 0, 0, tzinfo=self.UTC).astimezone(self.tz_FR)
        self._check(
            calendar,
            start_dt,
            end_dt,
            2 * 8,
            "for 4d including the CET -> CEST week end, Fri to Mon, you get 2d",
        )
