# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
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
        # Add city domain
        city_id = employee.address_id.city_id.id
        if not city_id:
            city_id = self.env.company.partner_id.city_id.id or False
        if city_id:
            domain.extend(
                [
                    "|",
                    ("city_ids", "=", city_id),
                    ("city_ids", "=", False),
                ]
            )
        return domain
