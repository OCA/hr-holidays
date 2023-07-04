# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.tools.float_utils import float_round


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    allow_credit = fields.Boolean(
        help=(
            "If set to true, employees would be able to make requests for this"
            " leave type even if allocated amount is insufficient."
        ),
    )
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
        help=("If set, limits credit allowance to employees of specified departments"),
    )

    def name_get(self):
        context_employee_id = self._context.get("employee_id")

        res = []
        for record in self:
            record_name = record.name

            extra = None
            if record.requires_allocation != "no" and context_employee_id:
                if record.virtual_remaining_leaves >= 0:
                    if record.allow_credit:
                        extra = _("%g available + credit")
                    else:
                        extra = _("%g available")
                    extra = extra % (
                        float_round(record.virtual_remaining_leaves, precision_digits=2)
                        or 0.0,
                    )
                elif record.allow_credit:
                    extra = _("%g used in credit") % (
                        float_round(
                            -record.virtual_remaining_leaves, precision_digits=2
                        )
                        or 0.0,
                    )

            if extra:
                record_name = _("%(name)s (%(extra)s)") % {
                    "name": record_name,
                    "extra": extra,
                }

            res.append((record.id, record_name))

        return res

    def get_employees_days(self, employee_ids, date=None):
        """Use this method to compute the virtual remaining leaves
        when the allow credit is enabled. In Odoo standard v15, it will
        calculate only when the allocation is set."""
        res = super().get_employees_days(employee_ids=employee_ids)
        for record in self:
            hr_leave = self.env["hr.leave"].search(
                [
                    ("employee_id", "in", employee_ids),
                    ("state", "in", ["confirm", "validate1", "validate"]),
                    ("holiday_status_id.id", "=", record.id),
                ]
            )
            allocations = (
                self.env["hr.leave.allocation"]
                .with_context(active_test=False)
                .search(
                    [
                        ("employee_id", "in", employee_ids),
                        ("state", "in", ["validate"]),
                        ("holiday_status_id", "in", record.ids),
                    ]
                )
            )

            for hr_leave_record in hr_leave:
                if record.allow_credit and not allocations:
                    virtual_remaining_leaves = res[hr_leave_record.employee_id.id][
                        record.id
                    ]["virtual_remaining_leaves"]
                    res[hr_leave_record.employee_id.id][record.id][
                        "virtual_remaining_leaves"
                    ] = (virtual_remaining_leaves - hr_leave_record.number_of_days)
        return res
