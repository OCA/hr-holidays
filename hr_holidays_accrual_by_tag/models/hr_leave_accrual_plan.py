# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class HrLeaveAccrualPlan(models.Model):
    _inherit = "hr.leave.accrual.plan"

    generate_allocation_category_ids = fields.Many2many(
        comodel_name="hr.employee.category",
        relation="hr_leave_accrual_category_rel",
        string="Generate allocations by tag",
        help="When one of these tags is added to an employee: "
        "an accrual allocation for the employee is created.\n"
        "When one of these tags is removed from an employee: "
        "the corresponding accrual allocation is ended.\n",
    )
    generate_allocation_default_status_id = fields.Many2one(
        comodel_name="hr.leave.type",
        check_company=True,
        string="Default Time Off Type for generated allocations",
        help="Type of the generated allocations.",
    )

    @api.constrains(
        "generate_allocation_default_status_id",
        "time_off_type_id",
    )
    def _check_generate_allocation_time_off_type(self):
        for plan in self:
            default_time_off_type = plan.generate_allocation_default_status_id
            time_off_type = plan.time_off_type_id
            if (
                default_time_off_type
                and time_off_type
                and time_off_type != default_time_off_type
            ):
                raise exceptions.ValidationError(
                    plan.env._(
                        "The Accrual Plan %(plan)s can only "
                        "generate Allocations of Type %(type)s",
                        plan=plan.display_name,
                        type=time_off_type.display_name,
                    )
                )
