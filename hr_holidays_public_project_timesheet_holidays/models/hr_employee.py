# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        if self.env.context.get("salary_simulation"):
            return employees
        employees.with_context(
            allowed_company_ids=employees.company_id.ids
        )._create_future_public_holiday_timesheets(employees)
        return employees

    def write(self, vals):
        employees_with_changed_address = self.env["hr.employee"]
        employees_to_unarchive = self.env["hr.employee"]
        if "address_id" in vals:
            employees_with_changed_address = self.filtered(
                lambda employee: employee.address_id.id != vals.get("address_id")
            )
        if vals.get("active"):
            employees_to_unarchive = self.filtered(lambda employee: not employee.active)

        result = super().write(vals)

        self_company = self.with_context(allowed_company_ids=self.company_id.ids)
        if "active" in vals:
            if vals.get("active"):
                employees_to_unarchive.with_env(
                    self_company.env
                )._create_future_public_holiday_timesheets(employees_to_unarchive)
            else:
                self_company._delete_future_public_holiday_timesheets()
        elif "address_id" in vals and employees_with_changed_address:
            employees_with_changed_address.with_env(
                self_company.env
            )._delete_future_public_holiday_timesheets()
            employees_with_changed_address.with_env(
                self_company.env
            )._create_future_public_holiday_timesheets(employees_with_changed_address)

        return result

    def _delete_future_public_holiday_timesheets(self):
        timesheets = (
            self.env["account.analytic.line"]
            .sudo()
            .search(
                [
                    ("employee_id", "in", self.ids),
                    ("public_holiday_line_id", "!=", False),
                    ("date", ">=", fields.Date.today()),
                ]
            )
        )
        timesheets.write({"public_holiday_line_id": False})
        timesheets.unlink()

    def _create_future_public_holiday_timesheets(self, employees):
        holiday_lines = self.env["calendar.public.holiday.line"].search(
            [("date", ">=", fields.Date.today())]
        )
        holiday_lines._generate_public_holiday_timesheets(employees)
