# Copyright 2024 APSL-Nagarro - Antoni Marroig Campomar
# Copyright 2025 Grupo Isonor - Alexandre D. Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_consumed_leaves(self, leave_types, target_date=False, ignore_future=False):
        """Calculate consumed leaves with natural day support via context.


        We need to handle natural_day leave types by using context instead of
        directly modifying the request_unit field to avoid ORM violations.
        """
        natural_day_types = leave_types.filtered(
            lambda t: t.request_unit == "natural_day"
        )
        if natural_day_types:
            # Use context to signal natural day calculation without field modification
            ctx = dict(
                self.env.context,
                mod_holidays_status_ids=natural_day_types.ids,
                natural_day_computation=True,
            )
            return super(HrEmployee, self.with_context(**ctx))._get_consumed_leaves(
                leave_types, target_date, ignore_future
            )
        return super()._get_consumed_leaves(leave_types, target_date, ignore_future)
