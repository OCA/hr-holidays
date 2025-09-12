# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import ValidationError


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    def write(self, values):
        # The logic is based on the original method in the hr_holidays module
        res = super().write(values)
        if (
            "number_of_days_display" not in values
            and "number_of_hours_display" not in values
        ):
            return res
        consumed_leaves = self.employee_id._get_consumed_leaves(
            leave_types=self.holiday_status_id
        )
        for allocation in self:
            current_excess = (
                dict(consumed_leaves[1])
                .get(allocation.employee_id, {})
                .get(allocation.holiday_status_id, {})
                .get("excess_days", {})
            )
            total_current_excess = sum(
                leave_date["amount"]
                for leave_date in current_excess.values()
                if not leave_date["is_virtual"]
            )
            lt = allocation.holiday_status_id
            # If the employee is not allowed to have negative holiday
            # credit, we must ensure that the allocation cannot be reduced
            # leaving negative balance for said employee
            if not lt._is_holiday_credit_allowed(allocation.employee_id):
                if lt.allows_negative and total_current_excess > 0:
                    raise ValidationError(
                        self.env._(
                            "You cannot reduce the duration below the duration "
                            "of leaves already taken by the employee."
                        )
                    )
        return res
