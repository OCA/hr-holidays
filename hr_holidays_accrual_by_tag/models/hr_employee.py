from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee in employees:
            employee._assign_accrual_plans_by_tags()
        return employees

    def write(self, vals):
        res = super().write(vals)
        if "category_ids" in vals:
            for employee in self:
                employee._assign_accrual_plans_by_tags()
        return res

    def _assign_accrual_plans_by_tags(self):
        self.ensure_one()
        employee_tag_names = self.category_ids.mapped("name")
        accrual_allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "=", False),
                ("holiday_type", "=", "category"),
                ("accrual_plan_id", "!=", False),
            ]
        )

        for allocation in accrual_allocations:
            existing_assignment = self.env["hr.leave.allocation"].search(
                [
                    ("employee_id", "=", self.id),
                    ("accrual_plan_id", "=", allocation.accrual_plan_id.id),
                    ("date_to", "=", False),
                ],
                limit=1,
            )
            if (
                allocation.category_id.name in employee_tag_names
                and not existing_assignment
            ):
                new_allocation = {
                    "name": allocation.name,
                    "holiday_type": "employee",
                    "holiday_status_id": allocation.holiday_status_id.id,
                    "notes": allocation.notes,
                    "number_of_days": allocation.number_of_days,
                    "parent_id": allocation.id,
                    "employee_id": self.id,
                    "employee_ids": [(6, 0, [self.id])],
                    "state": "confirm",
                    "allocation_type": allocation.allocation_type,
                    "date_from": fields.Date.context_today(self),
                    "accrual_plan_id": allocation.accrual_plan_id.id,
                }
                childs = allocation.with_context(
                    mail_notify_force_send=False, mail_activity_automation_skip=True
                ).create(new_allocation)
                childs.action_validate()
            elif (
                allocation.category_id.name not in employee_tag_names
                and existing_assignment
            ):
                existing_assignment.date_to = fields.Date.context_today(self)
