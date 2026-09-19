# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveAllocationGenerateMultiWizard(models.TransientModel):
    _inherit = "hr.leave.allocation.generate.multi.wizard"

    contract_date_enforce = fields.Boolean()

    def _prepare_allocation_values(self, employees):
        self.ensure_one()
        if not self.contract_date_enforce:
            return super()._prepare_allocation_values(employees)
        if self.date_to:
            new_employees = employees.filtered(
                lambda emp, date_to=self.date_to: emp.first_contract_date
                and emp.first_contract_date <= date_to
            )
        else:
            new_employees = employees.filtered(lambda emp: emp.first_contract_date)
        values = super()._prepare_allocation_values(new_employees)
        for employee, vals in zip(new_employees, values, strict=False):
            vals["date_from"] = max(self.date_from, employee.first_contract_date)
        return values
