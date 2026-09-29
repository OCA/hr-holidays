# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

TIMESHEET_TRIGGER_FIELDS = {"public_holiday_region_id", "active"}


class HrWorkLocation(models.Model):
    _inherit = "hr.work.location"

    def write(self, vals):
        """Rebuild the timesheets when the work location is relinked.

        The public holiday region of everybody working here is derived
        from the work location, so relinking it moves their region-scoped
        days without any version write the timesheet trigger could see. The
        mirrors are resynchronised first, through the trigger below this
        one.
        """
        res = super().write(vals)
        if TIMESHEET_TRIGGER_FIELDS.intersection(vals):
            employees = (
                self.env["hr.employee"]
                .sudo()
                .search([("version_ids.work_location_id", "in", self.ids)])
            )
            employees._refresh_future_public_holiday_timesheets()
        return res
