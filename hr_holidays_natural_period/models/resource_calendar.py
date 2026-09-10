# Copyright 2020-2021 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, time

from dateutil import rrule
from pytz import timezone

from odoo import models
from odoo.tools.float_utils import float_is_zero, float_round
from odoo.tools.intervals import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _get_attendance_intervals_days_data(self, attendance_intervals):
        # replace function to avoid division by zero
        # it occurs when the calendar has no attendance intervals
        # i.e no working days(weekends)
        # meta is a recordset of resource.calendar.attendance
        # but in the function _natural_period_intervals_batch
        # we are passing an empty recordset
        if not self.env.context.get("natural_period"):
            return super()._get_attendance_intervals_days_data(attendance_intervals)
        day_hours = defaultdict(float)
        day_days = defaultdict(float)
        for start, stop, meta in attendance_intervals:
            interval_hours = (stop - start).total_seconds() / 3600
            if meta and not float_is_zero(
                sum(meta.mapped("duration_hours")), precision_digits=2
            ):
                interval_days = (
                    sum(meta.mapped("duration_days"))
                    * interval_hours
                    / sum(meta.mapped("duration_hours"))
                )
            else:
                interval_days = interval_hours / 24  # hours on a day
            day_hours[start.date()] += interval_hours
            day_days[start.date()] += interval_days
        # Round each calendar day to the nearest natural period unit before summing.
        # When compute_leaves=True, existing work-schedule leaves are subtracted from
        # the 24h natural-day intervals, producing fractions (e.g. 15h/24h = 0.625).
        # Since natural period counts whole calendar days, any remaining portion ≥ 0.5
        # of a unit must round up to a full unit, and days fully absorbed by a public
        # holiday (0 remaining) stay at 0.
        old_request_unit = self.env.context.get("old_request_unit", "natural_day")
        unit = 0.5 if old_request_unit in ("natural_day_half_day", "half_day") else 1.0
        return {
            "days": float_round(
                sum(
                    float_round(day_days[day], precision_rounding=unit)
                    for day in day_days
                ),
                precision_rounding=0.001,
            ),
            "hours": sum(day_hours.values()),
        }

    def _exist_interval_in_date(self, intervals, date):
        for interval in intervals:
            if interval[0].date() == date:
                return True
        return False

    def _natural_period_intervals_batch(self, start_dt, end_dt, intervals, resources):
        # Re-define start_dt and end_dt to ensure that we always iterate through the
        # last day.
        start_date = start_dt.date()
        end_date = end_dt.date()
        old_request_unit = self.env.context.get("old_request_unit")
        # Fix: if old_request_unit == 'day' and self.env.context.get('natural_period'):
        # old_request_unit = 'natural_day'
        if old_request_unit == "day" and self.env.context.get("natural_period"):
            old_request_unit = "natural_day"
        end_time = time.max if old_request_unit == "natural_day" else time(12, 0, 0)
        for resource in resources or []:
            tz = timezone(resource.tz)
            attendances = []
            # For natural days, create intervals for ALL days
            for day in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
                attendances.append(
                    (
                        datetime.combine(day.date(), time.min).replace(tzinfo=tz),
                        datetime.combine(day.date(), end_time).replace(tzinfo=tz),
                        # It is very important to use .new() so that https://github.com/odoo/odoo/blob/63b7407b3cb02603e9d0f57b9f336c1c9af3074d/addons/resource/models/resource_calendar.py#L566
                        # can execute the `any()` correctly and take these "virtual"
                        # records into account
                        # Related to https://github.com/odoo/odoo/commit/5588631d49e1ed6fb0ef1b433e94d29c271f82d0
                        self.env["resource.calendar.attendance"].new(),
                    )
                )
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
