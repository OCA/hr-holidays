# Copyright 2020-2021 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, timedelta
from datetime import time as datetime_time

from pytz import timezone

from odoo import models
from odoo.tools.float_utils import float_round

from odoo.addons.resource.models.utils import Intervals


class ResourceCalendar(models.Model):
    """Resource calendar helpers for natural day intervals."""

    _inherit = "resource.calendar"

    def _get_attendance_intervals_days_data(self, attendance_intervals):
        """
        Calculate days and hours data from attendance intervals.

        This override prevents division by zero errors when the calendar has no
        attendance intervals (e.g., weekends-only periods). For natural period
        calculations, we pass empty recordsets as metadata in fake intervals.

        Args:
            attendance_intervals: Intervals with (start, stop, meta) tuples

        Returns:
            Dict: Contains 'days' and 'hours' totals with proper rounding
        """
        if not self.env.context.get("natural_period"):
            return super()._get_attendance_intervals_days_data(attendance_intervals)
        day_hours = defaultdict(float)
        day_days = defaultdict(float)
        for start, stop, meta in attendance_intervals:
            interval_hours = (stop - start).total_seconds() / 3600.0
            if meta:
                total_duration_days = sum(meta.mapped("duration_days"))
                total_duration_hours = sum(meta.mapped("duration_hours"))
                if total_duration_hours > 0:
                    interval_days = (
                        total_duration_days * interval_hours / total_duration_hours
                    )
                else:
                    interval_days = interval_hours / 24.0
            else:
                interval_days = interval_hours / 24.0
            day_hours[start.date()] += interval_hours
            day_days[start.date()] += interval_days

        return {
            "days": float_round(sum(day_days.values()), precision_rounding=0.001),
            "hours": sum(day_hours.values()),
        }

    def _natural_period_intervals_batch(
        self, start_dt: datetime, end_dt: datetime, intervals: dict, resources
    ) -> dict:
        """
        Add fake intervals for non-working days to enable natural period calculations.

        For natural period calculations, we need to count all calendar days
        (including weekends) as "working days". This method adds full-day intervals
        for any missing dates in the period.

        Args:
            start_dt: Start datetime for the period
            end_dt: End datetime for the period
            intervals: Existing attendance intervals by resource
            resources: Resource recordset to process

        Returns:
            Dict: Updated intervals with added natural period intervals
        """
        # Normalize to full days to ensure complete iteration and handle tz properly
        cal_tz = timezone(self.tz or "UTC")
        if start_dt.tzinfo:
            start_local = start_dt.astimezone(cal_tz)
        else:
            start_local = cal_tz.localize(start_dt)
        if end_dt.tzinfo:
            end_local = end_dt.astimezone(cal_tz)
        else:
            end_local = cal_tz.localize(end_dt)
        start_date = start_local.date()
        end_date = end_local.date()

        # Precompute public holiday dates when requested
        ph_dates = set()
        if self.env.context.get("exclude_public_holidays"):
            ph_dates = set(
                self.env["hr.holidays.public"]
                .get_holidays_list(
                    start_dt=start_date,
                    end_dt=end_date,
                    employee_id=self.env.context.get("employee_id"),
                )
                .mapped("date")
            )

        for resource in resources or []:
            interval_resource = intervals[resource.id]
            tz = cal_tz
            attendances = (
                list(interval_resource._items) if interval_resource._items else []
            )

            # Create O(1) lookup set for existing dates
            existing_dates = {interval[0].date() for interval in attendances}

            # Generate full-day intervals for missing dates in batch
            # skipping public holidays
            missing_intervals = []
            current = start_date
            while current <= end_date:
                if current not in existing_dates and current not in ph_dates:
                    start = tz.localize(datetime.combine(current, datetime_time.min))
                    stop = tz.localize(datetime.combine(current, datetime_time.max))
                    missing_intervals.append(
                        (start, stop, self.env["resource.calendar.attendance"])
                    )
                current = current + timedelta(days=1)

            # Add missing intervals and rebuild Intervals object
            attendances.extend(missing_intervals)
            intervals[resource.id] = Intervals(attendances)

        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources=resources,
            domain=domain,
            tz=tz,
            lunch=lunch,
        )
        if self.env.context.get("natural_period"):
            return self._natural_period_intervals_batch(
                start_dt, end_dt, res, resources
            )
        return res
