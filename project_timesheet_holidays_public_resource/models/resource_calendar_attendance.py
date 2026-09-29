# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

# Fields that change which days -- or how many hours -- a schedule works.
TIMESHEET_TRIGGER_FIELDS = {
    "dayofweek",
    "hour_from",
    "hour_to",
    "day_period",
    "week_type",
    "display_type",
    "calendar_id",
}


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super().create(vals_list)
        attendances.calendar_id._update_public_holiday_timesheets()
        return attendances

    def write(self, vals):
        calendars = self.calendar_id
        res = super().write(vals)
        if TIMESHEET_TRIGGER_FIELDS.intersection(vals):
            (calendars | self.calendar_id)._update_public_holiday_timesheets()
        return res

    def unlink(self):
        calendars = self.calendar_id
        res = super().unlink()
        calendars._update_public_holiday_timesheets()
        return res
