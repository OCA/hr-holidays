# Copyright 2025 Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from odoo.tests.common import TransactionCase


class TestPublicHolidayExclusion(TransactionCase):
    """Test public holiday exclusion with natural days and timezone handling."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        # Create employee with timezone and resource calendar
        # Get default calendar or create one with standard working hours
        calendar = self.env.ref(
            "resource.resource_calendar_std", raise_if_not_found=False
        )
        if not calendar:
            calendar = self.env["resource.calendar"].create(
                {
                    "name": "Standard 40 hours/week",
                    "tz": "Europe/Madrid",
                    "attendance_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Monday Morning",
                                "dayofweek": "0",
                                "hour_from": 8,
                                "hour_to": 12,
                                "day_period": "morning",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Monday Afternoon",
                                "dayofweek": "0",
                                "hour_from": 13,
                                "hour_to": 17,
                                "day_period": "afternoon",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Tuesday Morning",
                                "dayofweek": "1",
                                "hour_from": 8,
                                "hour_to": 12,
                                "day_period": "morning",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Tuesday Afternoon",
                                "dayofweek": "1",
                                "hour_from": 13,
                                "hour_to": 17,
                                "day_period": "afternoon",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Wednesday Morning",
                                "dayofweek": "2",
                                "hour_from": 8,
                                "hour_to": 12,
                                "day_period": "morning",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Wednesday Afternoon",
                                "dayofweek": "2",
                                "hour_from": 13,
                                "hour_to": 17,
                                "day_period": "afternoon",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Thursday Morning",
                                "dayofweek": "3",
                                "hour_from": 8,
                                "hour_to": 12,
                                "day_period": "morning",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Thursday Afternoon",
                                "dayofweek": "3",
                                "hour_from": 13,
                                "hour_to": 17,
                                "day_period": "afternoon",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Friday Morning",
                                "dayofweek": "4",
                                "hour_from": 8,
                                "hour_to": 12,
                                "day_period": "morning",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Friday Afternoon",
                                "dayofweek": "4",
                                "hour_from": 13,
                                "hour_to": 17,
                                "day_period": "afternoon",
                            },
                        ),
                    ],
                }
            )

        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "tz": "Europe/Madrid",
                "resource_calendar_id": calendar.id,
            }
        )

        # Check if hr_holidays_public is installed
        self.has_public_holidays = "hr.holidays.public" in self.env

        # Create leave types - only set exclude_public_holidays if field exists
        leave_type_vals_exclude = {
            "name": "Natural Days - Exclude Holidays",
            "request_unit": "natural_day",
            "requires_allocation": "no",  # No allocation needed for testing
        }
        leave_type_vals_include = {
            "name": "Natural Days - Include Holidays",
            "request_unit": "natural_day",
            "requires_allocation": "no",  # No allocation needed for testing
        }

        # Only add exclude_public_holidays field if hr_holidays_public is installed
        LeaveType = self.env["hr.leave.type"]
        if self.has_public_holidays and "exclude_public_holidays" in LeaveType._fields:
            leave_type_vals_exclude["exclude_public_holidays"] = True
            leave_type_vals_include["exclude_public_holidays"] = False

        self.leave_type_exclude = LeaveType.create(leave_type_vals_exclude)
        self.leave_type_include = LeaveType.create(leave_type_vals_include)

        # Create public holiday if hr_holidays_public is installed
        if "hr.holidays.public" in self.env:
            # Create a public holiday for testing
            public_holiday = self.env["hr.holidays.public"].create(
                {
                    "name": "Test Holiday",
                    "year": datetime.now().year,
                }
            )
            # Add a holiday line for tomorrow
            tomorrow = datetime.now().date() + timedelta(days=1)
            self.env["hr.holidays.public.line"].create(
                {
                    "name": "Test Holiday Day",
                    "date": tomorrow,
                    "holidays_id": public_holiday.id,
                }
            )
            self.holiday_date = tomorrow
        else:
            self.holiday_date = None

    def test_natural_days_with_timezone_aware_dates(self):
        """Test that natural day calculation works with timezone-aware dates."""
        # Odoo expects naive UTC datetimes when creating records
        # Use specific dates to avoid weekend issues
        date_from = datetime(2025, 1, 13, 8, 0, 0)  # Monday
        date_to = datetime(2025, 1, 16, 16, 0, 0)  # Thursday afternoon

        leave = (
            self.env["hr.leave"]
            .with_context(default_date_from=date_from, default_date_to=date_to)
            .create(
                {
                    "name": "Test Leave",
                    "holiday_status_id": self.leave_type_include.id,
                    "employee_id": self.employee.id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "request_date_from": date_from.date(),
                    "request_date_to": date_to.date(),
                }
            )
        )

        # Ensure the record is properly saved
        self.env.cr.flush()

        # Should not raise timezone comparison error
        days, hours = leave._get_duration()

        # Natural days should count all calendar days (Mon, Tue, Wed, Thu)
        self.assertGreaterEqual(
            days, 3.0, f"Should count at least 3 natural days, got {days}"
        )

    def test_public_holiday_exclusion_flag_false(self):
        """Test that public holidays are counted when exclude_public_holidays=False."""
        if not self.has_public_holidays or not self.holiday_date:
            self.skipTest("hr_holidays_public not installed")

        # Create leave spanning the public holiday (naive UTC)
        date_from = datetime.combine(
            self.holiday_date - timedelta(days=1), datetime.min.time()
        )
        date_to = datetime.combine(
            self.holiday_date + timedelta(days=1), datetime.max.time()
        )
        date_to = datetime.combine(
            self.holiday_date + timedelta(days=1), datetime.max.time()
        ).replace(tzinfo=dt_timezone.utc)

        leave = self.env["hr.leave"].create(
            {
                "name": "Test Leave Including Holiday",
                "holiday_status_id": self.leave_type_include.id,
                "employee_id": self.employee.id,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

        days, hours = leave._get_duration()

        # Should count all 3 days including the public holiday
        self.assertEqual(days, 3.0, "Should count public holiday as natural day")

    def test_public_holiday_exclusion_flag_true(self):
        """Test that public holidays are excluded when exclude_public_holidays=True."""
        if not self.has_public_holidays or not self.holiday_date:
            self.skipTest("hr_holidays_public not installed")

        # Create leave spanning the public holiday (naive UTC)
        date_from = datetime.combine(
            self.holiday_date - timedelta(days=1), datetime.min.time()
        )
        date_to = datetime.combine(
            self.holiday_date + timedelta(days=1), datetime.max.time()
        )
        date_to = datetime.combine(
            self.holiday_date + timedelta(days=1), datetime.max.time()
        ).replace(tzinfo=dt_timezone.utc)

        leave = self.env["hr.leave"].create(
            {
                "name": "Test Leave Excluding Holiday",
                "holiday_status_id": self.leave_type_exclude.id,
                "employee_id": self.employee.id,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

        days, hours = leave._get_duration()

        # Should exclude the public holiday, counting only 2 days
        self.assertEqual(days, 2.0, "Should exclude public holiday from count")

    def test_onchange_no_timezone_error(self):
        """Test that onchange doesn't raise timezone comparison errors."""
        # Create a leave and trigger onchange
        leave = self.env["hr.leave"].new(
            {
                "holiday_status_id": self.leave_type_include.id,
                "employee_id": self.employee.id,
            }
        )

        # Set dates to trigger duration computation (naive UTC)
        now = datetime.utcnow()
        leave.date_from = now
        leave.date_to = now + timedelta(days=2)

        # This should not raise a timezone comparison error
        try:
            leave._compute_duration()
            leave._compute_display_name()
        except TypeError as e:
            if "can't compare offset-naive and offset-aware" in str(e):
                self.fail("Timezone comparison error in onchange")
            raise

    def test_core_calendar_public_holidays_exclusion_natural_days(self):
        """Core calendar holidays are handled for natural-day leaves."""
        # Create a core public holiday on the employee's calendar
        ph_date = datetime(2025, 1, 14).date()
        calendar = self.employee.resource_calendar_id
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Core PH",
                "calendar_id": calendar.id,
                "resource_id": False,
                "date_from": datetime(
                    ph_date.year, ph_date.month, ph_date.day, 0, 0, 0
                ),
                "date_to": datetime(
                    ph_date.year, ph_date.month, ph_date.day, 23, 59, 59
                ),
            }
        )

        # Leave spanning 3 days (holiday in the middle)
        date_from = datetime(ph_date.year, ph_date.month, ph_date.day - 1, 0, 0, 0)
        date_to = datetime(ph_date.year, ph_date.month, ph_date.day + 1, 23, 59, 59)

        leave_inc = self.env["hr.leave"].new(
            {
                "name": "Include core PH",
                "holiday_status_id": self.leave_type_include.id,
                "employee_id": self.employee.id,
                "date_from": date_from,
                "date_to": date_to,
                "request_date_from": date_from.date(),
                "request_date_to": date_to.date(),
            }
        )
        days_inc, _ = leave_inc._get_duration()
        self.assertEqual(days_inc, 3.0, "Core PH should be counted when include=True")

        leave_exc = self.env["hr.leave"].new(
            {
                "name": "Exclude core PH",
                "holiday_status_id": self.leave_type_exclude.id,
                "employee_id": self.employee.id,
                "date_from": date_from,
                "date_to": date_to,
                "request_date_from": date_from.date(),
                "request_date_to": date_to.date(),
            }
        )
        days_exc, _ = leave_exc.with_context(
            exclude_public_holidays=True
        )._get_duration()
        self.assertEqual(days_exc, 2.0, "Core PH should be excluded when exclude=True")

    def test_no_double_exclusion_when_sources_overlap(self):
        """When both sources mark same date, exclude once."""
        if not self.has_public_holidays:
            self.skipTest("hr_holidays_public not installed")
        ph_date = datetime(2025, 1, 15).date()
        calendar = self.employee.resource_calendar_id
        # Core PH
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Core PH overlap",
                "calendar_id": calendar.id,
                "resource_id": False,
                "date_from": datetime(
                    ph_date.year, ph_date.month, ph_date.day, 0, 0, 0
                ),
                "date_to": datetime(
                    ph_date.year, ph_date.month, ph_date.day, 23, 59, 59
                ),
            }
        )
        # OCA PH
        year = self.env["hr.holidays.public"].create({"year": ph_date.year})
        self.env["hr.holidays.public.line"].create(
            {"name": "OCA PH overlap", "date": ph_date, "holidays_id": year.id}
        )
        df = datetime(ph_date.year, ph_date.month, ph_date.day - 1, 0, 0, 0)
        dt = datetime(ph_date.year, ph_date.month, ph_date.day + 1, 23, 59, 59)
        leave = self.env["hr.leave"].create(
            {
                "name": "Overlap leave",
                "holiday_status_id": self.leave_type_exclude.id,
                "employee_id": self.employee.id,
                "date_from": df,
                "date_to": dt,
            }
        )
        days, _ = leave._get_duration()
        self.assertEqual(days, 2.0, "Overlapping PH must be excluded only once")

    def test_regular_day_leave_respects_hr_holidays_public(self):
        """Regular 'day' leave must respect hr_holidays_public exclusion."""
        if not self.has_public_holidays:
            self.skipTest("hr_holidays_public not installed")
        ltype = self.env["hr.leave.type"].create(
            {
                "name": "Regular Day Excl",
                "request_unit": "day",
                "requires_allocation": "no",
                "exclude_public_holidays": True,
            }
        )
        ph_date = datetime(2025, 1, 16).date()
        year = self.env["hr.holidays.public"].create({"year": ph_date.year})
        self.env["hr.holidays.public.line"].create(
            {"name": "OCA PH", "date": ph_date, "holidays_id": year.id}
        )
        df = datetime(ph_date.year, ph_date.month, ph_date.day - 1, 0, 0, 0)
        dt = datetime(ph_date.year, ph_date.month, ph_date.day + 1, 23, 59, 59)
        leave = self.env["hr.leave"].create(
            {
                "name": "Regular day leave",
                "holiday_status_id": ltype.id,
                "employee_id": self.employee.id,
                "date_from": df,
                "date_to": dt,
            }
        )
        days, _ = leave._get_duration()
        self.assertEqual(
            days,
            2.0,
            "Regular day leave must exclude hr_holidays_public holidays",
        )

    def test_core_calendar_public_holidays_tz_boundary_natural_days(self):
        """Core calendar PH across UTC midnight map to local dates correctly."""
        calendar = self.employee.resource_calendar_id
        # PH spans 22:00 UTC on 14th to 02:00 UTC on 15th
        # In Europe/Madrid (UTC+1 in Jan), that's 23:00 (14th) to 03:00 (15th),
        # so it should cover both local dates 14th and 15th.
        start_utc = datetime(2025, 1, 14, 22, 0, 0)
        end_utc = datetime(2025, 1, 15, 2, 0, 0)
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Core PH TZ boundary",
                "calendar_id": calendar.id,
                "resource_id": False,
                "date_from": start_utc,
                "date_to": end_utc,
            }
        )

        # Leave spanning 4 local days around the PH (13th..16th)
        df = datetime(2025, 1, 13, 0, 0, 0)
        dt = datetime(2025, 1, 16, 23, 59, 59)

        leave_inc = self.env["hr.leave"].new(
            {
                "name": "Include core PH (tz boundary)",
                "holiday_status_id": self.leave_type_include.id,
                "employee_id": self.employee.id,
                "date_from": df,
                "date_to": dt,
                "request_date_from": df.date(),
                "request_date_to": dt.date(),
            }
        )
        days_inc, _ = leave_inc._get_duration()
        self.assertEqual(days_inc, 4.0, "Include=True should count all 4 days")

        leave_exc = self.env["hr.leave"].new(
            {
                "name": "Exclude core PH (tz boundary)",
                "holiday_status_id": self.leave_type_exclude.id,
                "employee_id": self.employee.id,
                "date_from": df,
                "date_to": dt,
                "request_date_from": df.date(),
                "request_date_to": dt.date(),
            }
        )
        days_exc, _ = leave_exc.with_context(
            exclude_public_holidays=True
        )._get_duration()
        self.assertEqual(
            days_exc,
            2.0,
            "Exclude=True should subtract both local PH dates (14th and 15th)",
        )
