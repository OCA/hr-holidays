from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        employees._assign_accrual_plans_by_tags()
        return employees

    def write(self, vals):
        res = super().write(vals)
        if "category_ids" in vals:
            self._assign_accrual_plans_by_tags()
        return res

    def _assign_accrual_plans_by_tags(self):
        accrual_plans = self.env["hr.leave.accrual.plan"].search(
            [
                ("generate_allocation_category_ids", "!=", False),
            ]
        )
        existing_assignments = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "in", self.ids),
                ("accrual_plan_id", "in", accrual_plans.ids),
                ("date_to", "=", False),
            ],
        )

        generate_new_allocations_values = []
        for employee in self:
            employee_tags = employee.category_ids

            for plan in accrual_plans:
                employee_assignment = fields.first(
                    existing_assignments.filtered(
                        lambda assignment, plan=plan, employee=employee: (
                            assignment.accrual_plan_id == plan
                            and assignment.employee_id == employee
                        )
                    )
                )
                holiday_status = plan.generate_allocation_default_status_id
                for category in plan.generate_allocation_category_ids:
                    if category in employee_tags and not employee_assignment:
                        generate_new_allocations_values.append(
                            {
                                "allocation_mode": "employee",
                                "allocation_type": "accrual",
                                "holiday_status_id": holiday_status.id,
                                "employee_ids": employee.ids,
                                "accrual_plan_id": plan.id,
                            }
                        )
                    elif category not in employee_tags and employee_assignment:
                        employee_assignment.date_to = fields.Date.context_today(
                            employee
                        )

        if generate_new_allocations_values:
            generate_new_allocations = self.env[
                "hr.leave.allocation.generate.multi.wizard"
            ].create(generate_new_allocations_values)
            for wizard in generate_new_allocations:
                wizard.action_generate_allocations()
