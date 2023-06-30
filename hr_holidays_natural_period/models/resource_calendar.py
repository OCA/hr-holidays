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
        self, start_dt, end_dt, resources=None, domain=None, tz=None
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt, end_dt=end_dt, resources=resources, domain=domain, tz=tz
        )
        if self.env.context.get("natural_period"):
            return self._natural_period_intervals_batch(
                start_dt, end_dt, res, resources
            )
        return res
