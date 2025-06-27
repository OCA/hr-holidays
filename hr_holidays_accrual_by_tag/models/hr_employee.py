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
        accrual_allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "=", False),
                ("holiday_type", "=", "category"),
                ("accrual_plan_id", "!=", False),
            ]
        )
        existing_assignments = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "in", self.ids),
                ("accrual_plan_id", "in", accrual_allocations.accrual_plan_id.ids),
                ("date_to", "=", False),
            ],
        )

        new_allocations_values = []
        for employee in self:
            employee_tags = employee.category_ids

            for allocation in accrual_allocations:
                employee_assignment = fields.first(
                    existing_assignments.filtered(
                        lambda assignment, allocation=allocation, employee=employee: (
                            assignment.accrual_plan_id == allocation.accrual_plan_id
                            and assignment.employee_id == employee
                        )
                    )
                )
                if allocation.category_id in employee_tags and not employee_assignment:
                    new_allocations_values.append(
                        {
                            "name": allocation.name,
                            "holiday_type": "employee",
                            "holiday_status_id": allocation.holiday_status_id.id,
                            "notes": allocation.notes,
                            "number_of_days": allocation.number_of_days,
                            "parent_id": allocation.id,
                            "employee_id": employee.id,
                            "employee_ids": [(6, 0, employee.ids)],
                            "state": "confirm",
                            "allocation_type": allocation.allocation_type,
                            "date_from": fields.Date.context_today(employee),
                            "accrual_plan_id": allocation.accrual_plan_id.id,
                        }
                    )
                elif (
                    allocation.category_id not in employee_tags and employee_assignment
                ):
                    employee_assignment.date_to = fields.Date.context_today(employee)

        if new_allocations_values:
            new_allocations = (
                self.env["hr.leave.allocation"]
                .with_context(
                    mail_notify_force_send=False,
                    mail_activity_automation_skip=True,
                )
                .create(new_allocations_values)
            )
            new_allocations.action_validate()
