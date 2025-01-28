# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_domain_from_get_unusual_days(self, date_from, date_to=None):
        domain = super()._get_domain_from_get_unusual_days(
            date_from=date_from, date_to=date_to
        )
        # Use the employee of the user or the one who has the context
        employee_id = self.env.context.get("employee_id", False)
        employee = (
            self.env["hr.employee"].browse(employee_id)
            if employee_id
            else self.env.user.employee_id
        )
        # Add work location domain
        work_location = employee.work_location_id.id
        if work_location:
            domain.extend(
                [
                    "|",
                    ("work_location_ids", "=", work_location),
                    ("work_location_ids", "=", False),
                ]
            )
        return domain
