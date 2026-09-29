# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.fields import Domain


class CalendarPublicHolidayRegion(models.Model):
    """Every employee is assigned a public holiday region.

    The assignment is derived from the work location of each version
    (contract), so the mapping is maintained once, on the work location.
    """

    _inherit = "calendar.public.holiday.region"

    def _get_assigned_employees(self):
        """Everybody assigned here under any of their contracts."""
        return (
            self.env["hr.employee"]
            .sudo()
            .search(Domain("version_ids.public_holiday_region_id", "in", self.ids))
        )
