# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from collections import defaultdict

from odoo import models
from odoo.tools import float_utils

HOURS_PER_DAY = 8
ROUNDING_FACTOR = 9600


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _get_days_data(self, intervals, day_total):
        """
        OVERWRITE: Calculate number of days against company hours per day.
        """
        day_hours = defaultdict(float)
        for start, stop, _ in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        hours_per_day = self.company_id.resource_calendar_id.hours_per_day
        days = sum(
            float_utils.round(
                ROUNDING_FACTOR * day_hours[day] / hours_per_day or day_total[day]
            )
            / ROUNDING_FACTOR
            if day_total[day]
            else 0
            for day in day_hours
        )
        return {
            "days": days,
            "hours": sum(day_hours.values()),
        }
