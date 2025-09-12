# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    creditable_employee_ids = fields.Many2many(
        string="Creditable Employees",
        comodel_name="hr.employee",
        help="If set, limits credit allowance to specified employees",
    )
    creditable_employee_category_ids = fields.Many2many(
        string="Creditable Employee Tags",
        comodel_name="hr.employee.category",
        help=(
            "If set, limits credit allowance to employees with at least one of"
            " specified tags"
        ),
    )
    creditable_department_ids = fields.Many2many(
        string="Creditable Departments",
        comodel_name="hr.department",
        help="If set, limits credit allowance to employees of specified departments",
    )

    @api.onchange("requires_allocation", "allocation_validation_type")
    def _onchange_allow_credit(self):
        if self.requires_allocation == "no" or self.allocation_validation_type == "no":
            self.allows_negative = False
            self.max_allowed_negative = 0.0

    @api.onchange("allows_negative")
    def _onchange_max_allowed_negative(self):
        if not self.allows_negative:
            self.max_allowed_negative = 0.0

    def get_allocation_data(self, employees, target_date=None):
        # If the leave type allows negative balance but only for some
        # employees, we need to adjust the max_allowed_negative value
        # accordingly in the allocation data result. For employees that are not
        # allowed to have negative balance, we set it to 0
        result = super().get_allocation_data(employees, target_date=target_date)
        negative_cond_types = self.env["hr.leave.type"].search(
            [
                ("allows_negative", "=", True),
                "|",
                ("creditable_employee_ids", "!=", False),
                "|",
                ("creditable_employee_category_ids", "!=", False),
                ("creditable_department_ids", "!=", False),
            ]
        )
        for employee in result:
            negative_cond_types_no_credit = negative_cond_types.filtered(
                lambda lt, emp=employee: not lt._is_holiday_credit_allowed(emp)
            )
            for leave_data in result[employee]:
                if leave_data[0] in negative_cond_types_no_credit.mapped("name"):
                    leave_data[1]["max_allowed_negative"] = 0.0
        return result

    def _is_holiday_credit_allowed(self, employee=None):
        # Determine if the given employee is allowed to have holiday credit for
        # this leave type, depending on the creditable_employee_ids,
        # creditable_employee_category_ids and creditable_department_ids fields
        self.ensure_one()
        if not employee:
            return True
        if self.creditable_employee_ids:
            if employee in self.creditable_employee_ids:
                return True
        if self.creditable_employee_category_ids:
            employee_category_ids = set(employee.category_ids.ids)
            allowed_category_ids = set(self.creditable_employee_category_ids.ids)
            if employee_category_ids & allowed_category_ids:
                return True
        if self.creditable_department_ids:
            if employee.department_id in self.creditable_department_ids:
                return True
        return not (
            self.creditable_employee_ids
            or self.creditable_employee_category_ids
            or self.creditable_department_ids
        )

    @api.depends("requires_allocation", "max_leaves", "virtual_remaining_leaves")
    def _compute_valid(self):
        # The logic is based off the original method in the hr_holidays module
        res = super()._compute_valid()
        date_from = self._context.get("default_date_from", fields.Datetime.today())
        date_to = self._context.get("default_date_to", fields.Datetime.today())
        employee_id = self._context.get(
            "default_employee_id",
            self._context.get("employee_id", self.env.user.employee_id.id),
        )
        for leave_type in self:
            if leave_type.requires_allocation == "yes":
                allocations = self.env["hr.leave.allocation"].search(
                    [
                        ("holiday_status_id", "=", leave_type.id),
                        ("employee_id", "=", employee_id),
                        ("date_from", "<=", date_from),
                        "|",
                        ("date_to", ">=", date_to),
                        ("date_to", "=", False),
                    ]
                )
                allowed_excess = (
                    leave_type.max_allowed_negative if leave_type.allows_negative else 0
                )
                if allowed_excess > 0:
                    employee = self.env["hr.employee"].browse(employee_id)
                    # If the employee is not allowed to have holiday credit,
                    # we filter out allocations that have no remaining leaves,
                    # without considering the negative balance
                    if not leave_type._is_holiday_credit_allowed(employee):
                        allocations = allocations.filtered(
                            lambda alloc: alloc.allocation_type == "accrual"
                            or (
                                alloc.max_leaves > 0
                                and (alloc.max_leaves - alloc.leaves_taken) > 0
                            )
                        )
                        leave_type.has_valid_allocation = bool(allocations)
        return res
