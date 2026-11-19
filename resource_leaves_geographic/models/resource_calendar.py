# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import models
from odoo.fields import Domain


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _leave_intervals_batch(
        self, start_dt, end_dt, resources_per_tz=None, domain=None
    ):
        # If the employee’s address is obtained from the context, we will add the
        # 'company holidays' filter to the domain
        employee_address_id = self.env.context.get("employee_address_id")
        if employee_address_id:
            partner = self.env["res.partner"].browse(employee_address_id)
            domain += Domain(
                [
                    ("resource_id", "=", False),
                    "|",
                    ("state_ids", "=", False),
                    ("state_ids", "in", partner.state_id.ids),
                ]
            )
        return super()._leave_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources_per_tz=resources_per_tz,
            domain=domain,
        )
