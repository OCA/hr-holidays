# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None
    ):
        result = super()._attendance_intervals_batch(
            start_dt, end_dt, resources=resources, domain=domain, tz=tz
        )
        if self.env.context.get("exclude_public_holidays") and resources:
            return self._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, result, resources, tz
            )
        return result
