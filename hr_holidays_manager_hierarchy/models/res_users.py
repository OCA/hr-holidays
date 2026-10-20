# Copyright 2026 Antoni Marroig (APSL-Nagarro) <antoni.marroig@nagarro.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_hierarchy_subordinates(self):
        """Employees below the user in the hierarchy, excluding their own."""
        self.ensure_one()
        own_employees = self.employee_ids
        return (
            self.env["hr.employee"]
            .sudo()
            .with_context(active_test=False)
            .search([("id", "child_of", own_employees.ids)])
            - own_employees
        )
