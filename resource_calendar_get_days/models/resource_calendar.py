from odoo import models
from collections import defaultdict
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
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        
        # compute number of days as quarters
        hours_per_day = self.company_id.resource_calendar_id.hours_per_day
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / hours_per_day or day_total[day]) / ROUNDING_FACTOR if day_total[day] else 0
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }