# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from collections import defaultdict

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        # Upstream searches public holidays directly in some cases (e.g.
        # single-day leaves of flexible employees), skipping
        # ``_leave_intervals_batch``. Compute durations with the employee's
        # State in context, so those searches ignore other States' holidays.
        leaves_by_state = defaultdict(lambda: self.browse())
        for leave in self:
            state = leave.employee_id.sudo().address_id.state_id
            leaves_by_state[state.id] |= leave
        result = {}
        for state_id, leaves in leaves_by_state.items():
            result.update(
                super(
                    HrLeave,
                    leaves.with_context(resource_leaves_geographic_state_id=state_id),
                )._get_durations(
                    check_leave_type=check_leave_type,
                    resource_calendar=resource_calendar,
                )
            )
        return result
