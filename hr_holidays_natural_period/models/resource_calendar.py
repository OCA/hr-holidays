# Copyright 2020-2021 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, time

from dateutil import rrule
from pytz import timezone

from odoo import models
from odoo.tools.float_utils import float_round

from odoo.addons.resource.models.utils import Intervals


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
            if meta:
                interval_days = (
                    sum(meta.mapped("duration_days"))
                    * interval_hours
                    / sum(meta.mapped("duration_hours"))
                )
            else:
                interval_days = interval_hours / 24  # hours on a day
            day_hours[start.date()] += interval_hours
            day_days[start.date()] += interval_days

        return {
            # Round the number of days to the closest 16th of a day.
            "days": float_round(
                sum(day_days[day] for day in day_days), precision_rounding=0.001
            ),
            "hours": sum(day_hours.values()),
        }

    def _exist_interval_in_date(self, intervals, date):
        for interval in intervals:
            if interval[0].date() == date:
                return True
        return False

    def _natural_period_intervals_batch(self, start_dt, end_dt, intervals, resources):
        for resource in resources or []:
            interval_resource = intervals[resource.id]
            tz = timezone(resource.tz)
            attendances = []
            if len(interval_resource._items) > 0:
                attendances = interval_resource._items
            for day in rrule.rrule(rrule.DAILY, dtstart=start_dt, until=end_dt):
                exist_interval = self._exist_interval_in_date(attendances, day.date())
                if not exist_interval:
                    attendances.append(
                        (
                            datetime.combine(day.date(), time.min).replace(tzinfo=tz),
                            datetime.combine(day.date(), time.max).replace(tzinfo=tz),
                            self.env["resource.calendar.attendance"],
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
