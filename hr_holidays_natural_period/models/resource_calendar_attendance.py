# Copyright 2025 Extreme Micro S.L. - Óscar Fonseca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    def write(self, vals):
        res = super().write(vals)
        # Clear caches when attendance details change because:
        # 1. _natural_period_intervals_batch depends on attendance intervals
        # 2. _get_duration uses these intervals for leave duration calculations
        if any(
            key in vals
            for key in ["dayofweek", "hour_from", "hour_to", "date_from", "date_to"]
        ):
            self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        # Clear caches as attendance removal affects interval calculations
        self.env.registry.clear_cache()
        return res
