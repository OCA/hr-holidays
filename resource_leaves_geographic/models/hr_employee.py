# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, time

from dateutil.rrule import DAILY, rrule
from pytz import UTC

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_unusual_days(self, date_from, date_to=None):
        """Get the geographical unusual days belongs to employees"""
        res = super()._get_unusual_days(date_from, date_to=date_to)

        def dt_combiner(dt, tx):
            """Return a datetime object with the date converted to datetime

            :param dt: date string
            :param tx: time.min or time.max
            """
            return datetime.combine(fields.Date.from_string(dt), tx).replace(tzinfo=UTC)

        calendars = (
            self.mapped("resource_calendar_id") or self.env.company.resource_calendar_id
        )
        state_interval_map = calendars._get_general_time_off_intervals_by_state(
            domain=[
                ("state_ids", "in", self.mapped("address_id.state_id").ids),
                ("date_from", "<=", dt_combiner(date_to, time.max)),
                ("date_to", ">=", dt_combiner(date_from, time.min)),
            ],
            any_calendar=False,
        )
        local_leave_days = set()
        for state_interval_map in state_interval_map.values():
            for start, end, _rcl in state_interval_map:
                local_leave_days.update(
                    {
                        fields.Date.to_string(day.date())
                        for day in rrule(DAILY, start.date(), until=end.date())
                    }
                )

        for day in res.keys():
            if day in local_leave_days:
                res[day] = True
        return res
