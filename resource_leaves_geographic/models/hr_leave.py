# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from collections import defaultdict

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_public_holidays_domain(self, max_end, min_start):
        """Restrict public holidays to those applicable to the employee's address."""
        domain = super()._get_public_holidays_domain(max_end, min_start)
        domain += self.resource_calendar_id._get_public_holidays_extra_domain(
            self.employee_id.address_id.id
        )
        return domain

    def _create_leaves_from_split(self, leave_split, use_worked_days=False):
        # Leave splitting relies on work intervals, which must also account for
        # the employee's public holidays.
        _self = self.with_context(
            partner_id=self.employee_id.address_id.id,
            from_create_leaves_from_split=True,
        )
        return super(HrLeave, _self)._create_leaves_from_split(
            leave_split=leave_split, use_worked_days=use_worked_days
        )

    def _get_durations(
        self,
        check_work_entry_type=True,
        resource_calendar=None,
        additional_domain=None,
    ):
        # Compute each address group separately to prevent public holidays from
        # one address from affecting employees in another address.
        result = {}
        leaves_by_state = defaultdict(lambda: self.env["hr.leave"])
        for leave in self:
            address_id = leave.employee_id.address_id.id
            leaves_by_state[address_id] |= leave
        for address_id, leaves in leaves_by_state.items():
            leaves = leaves.with_context(partner_id=address_id)
            result.update(
                super(HrLeave, leaves)._get_durations(
                    check_work_entry_type=check_work_entry_type,
                    resource_calendar=resource_calendar,
                    additional_domain=additional_domain,
                )
            )
        return result
