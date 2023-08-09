# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    holiday_status_id = fields.Many2one(
        domain=[
            "|",
            ("has_valid_allocation", "=", True),
            "|",
            ("requires_allocation", "=", "no"),
            ("allow_credit", "=", True),
        ]
    )

    @api.constrains("state", "number_of_days", "holiday_status_id")
    def _check_holidays(self):
        uncreditable_requests = self.filtered(
            lambda holiday: not holiday._is_holiday_credit_allowed()
        )

        return super(HrLeave, uncreditable_requests)._check_holidays()

    def _check_overtime_deductible(self, leaves):
        uncreditable_leaves = leaves.filtered(
            lambda holiday: not holiday._is_holiday_credit_allowed()
        )
        return super()._check_overtime_deductible(uncreditable_leaves)

    def _is_holiday_credit_allowed(self):
        self.ensure_one()

        leave_type = self.holiday_status_id
        hr_leave_employees = set(self.employee_ids.ids)
        hr_leave_type_employees = set(leave_type.creditable_employee_ids.ids)
        check_same_employees = hr_leave_employees.issubset(hr_leave_type_employees)

        if not leave_type.allow_credit:
            return False

        if check_same_employees:
            return True

        if self.employee_id in (
            leave_type.creditable_employee_category_ids.mapped("employee_ids")
        ):
            return True

        if self.employee_id in (
            leave_type.creditable_department_ids.mapped("member_ids")
        ):
            return True

        return (
            not leave_type.creditable_employee_ids
            and not leave_type.creditable_employee_category_ids
            and not leave_type.creditable_department_ids
        )
