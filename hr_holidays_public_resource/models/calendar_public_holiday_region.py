# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

SYNC_TRIGGER_FIELDS = {"active", "company_id", "public_holiday_line_ids"}


class CalendarPublicHolidayRegion(models.Model):
    _inherit = "calendar.public.holiday.region"

    def write(self, vals):
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            # The public holidays of everybody working here change with the
            # assigned holidays, the company, or the region going away.
            # Writing the assignment from this side never touches
            # `calendar.public.holiday.line.write`, so the line-side trigger
            # cannot see it.
            self._get_assigned_employees()._trigger_public_holiday_resync()
        return res
