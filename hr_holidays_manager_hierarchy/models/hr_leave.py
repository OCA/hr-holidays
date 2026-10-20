# Copyright 2026 Antoni Marroig (APSL-Nagarro) <antoni.marroig@nagarro.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    in_manager_hierarchy = fields.Boolean(
        string="In My Team Hierarchy",
        compute="_compute_in_manager_hierarchy",
        search="_search_in_manager_hierarchy",
    )

    def _get_manager_hierarchy_domain(self):
        return [("employee_id", "child_of", self.env.user.employee_ids.ids)]

    def _compute_in_manager_hierarchy(self):
        team_leaves = self.filtered_domain(self._get_manager_hierarchy_domain())
        for leave in self:
            leave.in_manager_hierarchy = leave in team_leaves

    def _search_in_manager_hierarchy(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise NotImplementedError()
        domain = self._get_manager_hierarchy_domain()
        if (operator == "=") != value:
            return ["!"] + domain
        return domain

    def _get_manager_hierarchy_approvals(self, state):
        """Leaves the user can approve or refuse as a manager higher up in the
        hierarchy, with the same rights as the employee's time off manager."""
        if (
            state not in ("validate1", "validate", "refuse")
            or self.env.is_superuser()
            or self.env.user.has_group("hr_holidays.group_hr_holidays_user")
        ):
            return self.browse()
        subordinates = self.env.user._get_hierarchy_subordinates()
        return self.filtered(
            lambda leave: leave.holiday_type == "employee"
            and leave.employee_id in subordinates
            and leave.employee_id.leave_manager_id != self.env.user
            and not (state == "validate" and leave.validation_type == "hr")
        )

    def _check_approval_update(self, state):
        hierarchy_leaves = self._get_manager_hierarchy_approvals(state)
        hierarchy_leaves.check_access_rule("write")
        return super(HrLeave, self - hierarchy_leaves)._check_approval_update(state)

    def _check_double_validation_rules(self, employees, state):
        # The first approval of double validation leaves is reserved to the time
        # off manager: allow it also to the managers higher up in the hierarchy.
        if state == "validate1" and self.env.user.has_group(
            "hr_holidays.group_hr_holidays_responsible"
        ):
            employees -= self.env.user._get_hierarchy_subordinates()
        return super()._check_double_validation_rules(employees, state)
