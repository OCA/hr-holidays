from odoo import models
from collections import defaultdict
from odoo.tools import float_utils

# Default hour per day value. The one should
# only be used when the one from the calendar
# is not available.
HOURS_PER_DAY = 8
# This will generate 64th of days
ROUNDING_FACTOR = 64


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