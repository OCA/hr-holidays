# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, timedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_validity(self):
        # The logic is based off the original method in the hr_holidays module
        result = super()._check_validity()
        sorted_leaves = defaultdict(lambda: self.env["hr.leave"])
        for leave in self:
            sorted_leaves[(leave.holiday_status_id, leave.date_from.date())] |= leave
        for (leave_type, date_from), leaves in sorted_leaves.items():
            if leave_type.requires_allocation == "no":
                continue
            employees = self.env["hr.employee"]
            for leave in leaves:
                employees |= leave._get_employees_from_holiday_type()
            leave_data = leave_type.get_allocation_data(employees, date_from)
            if leave_type.allows_negative:
                for employee in employees:
                    # max_excess is retrieved from leave_data because it
                    # contains conditional values based on the employee for the
                    # max_allowed_negative field
                    max_excess = leave_data[employee][0][1]["max_allowed_negative"]
                    if (
                        leave_data[employee]
                        and leave_data[employee][0][1]["virtual_remaining_leaves"]
                        < -max_excess
                    ):
                        raise ValidationError(
                            _("There is no valid allocation to cover that request.")
                        )
                continue
        return result

    def _cancel_invalid_leaves(self):
        # The logic is based off the original method in the hr_holidays module
        res = super()._cancel_invalid_leaves()
        inspected_date = fields.Date.today() + timedelta(days=31)
        start_datetime = datetime.combine(fields.Date.today(), datetime.min.time())
        end_datetime = datetime.combine(inspected_date, datetime.max.time())
        concerned_leaves = self.search(
            [
                ("date_from", ">=", start_datetime),
                ("date_from", "<=", end_datetime),
                ("state", "in", ["confirm", "validate1", "validate"]),
            ],
            order="date_from desc",
        )
        accrual_allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "in", concerned_leaves.employee_id.ids),
                ("holiday_status_id", "in", concerned_leaves.holiday_status_id.ids),
                ("allocation_type", "=", "accrual"),
                ("date_from", "<=", end_datetime),
                "|",
                ("date_to", ">=", start_datetime),
                ("date_to", "=", False),
            ]
        )
        concerned_leaves = concerned_leaves.filtered(
            lambda leave: leave.holiday_status_id
            in accrual_allocations.holiday_status_id
        ).sorted("date_from", reverse=True)
        reason = _("the accruated amount is insufficient for that duration.")
        for leave in concerned_leaves:
            leave_type = leave.holiday_status_id
            date = leave.date_from.date()
            leave_type_data = leave_type.get_allocation_data(leave.employee_id, date)
            exceeding_duration = leave_type_data[leave.employee_id][0][1][
                "total_virtual_excess"
            ]
            # The excess_limit is retrieved from leave_type_data because it
            # contains conditional values based on the employee for the
            # max_allowed_negative field
            excess_limit = leave_type_data[leave.employee_id][0][1][
                "max_allowed_negative"
            ]
            if exceeding_duration > excess_limit:
                leave._force_cancel(reason, "mail.mt_note")
        return res
