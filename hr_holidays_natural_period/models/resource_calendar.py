# Copyright 2020-2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, time

from dateutil import rrule
from pytz import timezone

from odoo import models

from odoo.addons.resource.models.resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _exist_interval_in_date(self, intervals, date):
        for interval in intervals:
            if interval[0].date() == date:
                return True
        return False

    def _natural_period_intervals_batch(
        self, start_dt, end_dt, intervals, resources, tz=None
    ):
        end_time = (
            time.max
            if self.env.context.get("old_request_unit") == "natural_day"
            else time(12, 0, 0)
        )
        for resource in resources or []:
            interval_resource = intervals[resource.id]
            resource_tz = tz or timezone(resource.tz or self.tz)
            # Iterate through the days in the resource timezone: start_dt and end_dt
            # are usually in UTC, so their date can be the previous/next day (e.g.
            # an attendance starting at 00:00 in Europe/Madrid starts at 23:00 UTC
            # of the previous day).
            start_date = start_dt.astimezone(resource_tz).date()
            end_date = end_dt.astimezone(resource_tz).date()
            attendances = list(interval_resource._items)
            for day in rrule.rrule(
                rrule.DAILY,
                dtstart=datetime.combine(start_date, time.min),
                until=datetime.combine(end_date, time.min),
            ):
                exist_interval = self._exist_interval_in_date(attendances, day.date())
                if not exist_interval:
                    attendances.append(
                        (
                            resource_tz.localize(datetime.combine(day, time.min)),
                            resource_tz.localize(datetime.combine(day, end_time)),
                            self.env["resource.calendar.attendance"],
                        )
                    )
            intervals[resource.id] = Intervals(attendances)
        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt, end_dt=end_dt, resources=resources, domain=domain, tz=tz
        )
        if self.env.context.get("natural_period"):
            return self._natural_period_intervals_batch(
                start_dt, end_dt, res, resources, tz=tz
            )
        return res
