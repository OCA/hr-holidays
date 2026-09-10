# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


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
        string="Default Time Off Type for generated allocations",
        help="Type of the generated allocations.",
    )
