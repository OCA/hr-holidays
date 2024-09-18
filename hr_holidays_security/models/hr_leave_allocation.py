# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    private_name = fields.Char(groups="hr_holidays.group_hr_holidays_responsible")
    allowed_holyday_status_ids = fields.Many2many(
        comodel_name="hr.leave.type", compute="_compute_allowed_holyday_status_ids"
    )

    def _get_allowed_holyday_status_domain(self):
        if self.user_has_groups("hr_holidays.group_hr_holidays_user") or (
            self._user_is_bare_responsible()
            and self.employee_id.user_id != self.env.user
        ):
            return [("valid", "=", True), ("allocation_type", "!=", "no")]
        else:
            return [("valid", "=", True), ("allocation_type", "=", "fixed_allocation")]

    @api.depends("employee_id")
    def _compute_allowed_holyday_status_ids(self):
        """Responsibles can only do allocations on their team members but on
        themselves"""
        for allocation in self:
            allocation.allowed_holyday_status_ids = self.env["hr.leave.type"].search(
                allocation._get_allowed_holyday_status_domain()
            )

    @api.model
    def _user_is_bare_responsible(self):
        return self.env.user.has_group(
            "hr_holidays.group_hr_holidays_responsible"
        ) and not self.env.user.has_group("hr_holidays.group_hr_holidays_user")

    def _compute_description(self):
        self.check_access_rights("read")
        self.check_access_rule("read")
        if not self._user_is_bare_responsible():
            return super()._compute_description()
        for allocation in self:
            if (
                allocation.employee_id.user_id == self.env.user
                or allocation.manager_id == self.env.user
            ):
                allocation.name = allocation.sudo().private_name
            else:
                allocation.name = "*****"

    def _inverse_description(self):
        if not self._user_is_bare_responsible():
            return super()._inverse_description()
        for allocation in self:
            if (
                allocation.employee_id.user_id == self.env.user
                or allocation.manager_id == self.env.user
            ):
                allocation.sudo().private_name = allocation.name

    def _search_description(self, operator, value):
        if not self._user_is_bare_responsible():
            return super()._search_description(operator, value)
        domain = [("private_name", operator, value)]
        allocations = self.sudo().search(domain)
        return [("id", "in", allocations.ids)]

    def _check_approval_update(self, state):
        # Lift restrictions
        if not self.env.user.has_group("hr_holidays.group_hr_holidays_responsible"):
            return super()._check_approval_update(state)
        current_employee = self.env.user.employee_id
        if not current_employee:
            return
        for holiday in self:
            if state == "confirm":
                continue
            if self.env.user == holiday.employee_id.leave_manager_id:
                # use ir.rule based first access check: department, members, ...
                # (see security.xml)
                holiday.check_access_rule("write")
