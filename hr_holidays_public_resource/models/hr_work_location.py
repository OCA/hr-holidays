# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

SYNC_TRIGGER_FIELDS = {"public_holiday_region_id", "active"}


class HrWorkLocation(models.Model):
    _inherit = "hr.work.location"

    def write(self, vals):
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            # Relinking a work location moves everybody working there to
            # another public holiday region; the derived field on the
            # versions recomputes without a write of its own, so nothing else
            # can see the change.
            employees = (
                self.env["hr.employee"]
                .sudo()
                .search([("version_ids.work_location_id", "in", self.ids)])
            )
            employees._trigger_public_holiday_resync()
        return res
