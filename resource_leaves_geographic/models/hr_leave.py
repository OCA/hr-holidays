# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models
from odoo.fields import Domain


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_public_holidays_domain(self, max_end, min_start):
        domain = super()._get_public_holidays_domain(max_end, min_start)
        addresses = self.employee_id.mapped("address_id")
        if addresses:
            domain += Domain(
                [
                    ("country_id", "in", addresses.country_id.ids),
                    "|",
                    ("state_ids", "=", False),
                    ("state_ids", "in", addresses.state_id.ids),
                ]
            )
        return domain
