# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    leave_manager_ids = fields.Many2many(
        "res.users",
        string="Time Off Managers",
        store=True,
        readonly=False,
        help="""Select the users responsible for approving 'Time Off' of this employee.
        If empty, the approval is done by an Administrator
        or Approver (determined in settings/users).""",
    )

    @api.depends("parent_id", "leave_manager_ids")
    def _compute_leave_manager(self):
        for employee in self:
            if employee.leave_manager_ids:
                employee.leave_manager_id = employee.leave_manager_ids[0]
            else:
                return super()._compute_leave_manager()

    def _add_leave_manager_ids_in_group(self, values):
        if "leave_manager_ids" in values:
            approver_group = self.env.ref(
                "hr_holidays.group_hr_holidays_responsible", raise_if_not_found=False
            )
            manager_ids_to_add = set()
            for command in values["leave_manager_ids"]:
                command_type = command[0]
                if command_type == 4:
                    manager_ids_to_add.add(command[1])
                elif command_type == 6:
                    manager_ids_to_add.update(command[2])
            if manager_ids_to_add:
                approver_group.sudo().write(
                    {"users": [(4, manager_id) for manager_id in manager_ids_to_add]}
                )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self._add_leave_manager_ids_in_group(vals_list)
        return res

    def write(self, values):
        res = super().write(values)
        self._add_leave_manager_ids_in_group(values)
        return res
