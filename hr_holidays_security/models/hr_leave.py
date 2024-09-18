# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_approval_update(self, state):
        """Check if target state is achievable"""
        if (
            not self.env.user.has_group("hr_holidays.group_hr_holidays_responsible")
            or self.env.user.has_group("hr_holidays.group_hr_holidays_manager")
            or self.env.is_superuser()
        ):
            return super()._check_approval_update(state)
        # Do nothing
        if state == "confirm":
            return
        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group("hr_holidays.group_hr_holidays_user")
        is_responsible = self.env.user.has_group(
            "hr_holidays.group_hr_holidays_responsible"
        )

        for holiday in self:
            val_type = holiday.validation_type
            if state != "draft":
                if (
                    val_type == "no_validation"
                    and current_employee == holiday.employee_id
                ):
                    continue
                # use ir.rule based first access check: department, members, ...
                # (see security.xml)
                holiday.check_access_rule("write")
                # This handles states validate1 validate and refuse
                if holiday.employee_id == current_employee:
                    raise UserError(
                        _(
                            "Only a Time Off Manager can approve/refuse its own requests."
                        )
                    )
                if (
                    (state == "validate1" and val_type == "both")
                    or (state == "validate" and val_type == "manager")
                    and holiday.holiday_type == "employee"
                ):
                    if (
                        not is_officer
                        and self.env.user != holiday.employee_id.leave_manager_id
                    ):
                        raise UserError(
                            _(
                                "You must be either %s's manager or Time off Manager "
                                "to approve this leave"
                            )
                            % (holiday.employee_id.name)
                        )
                if (
                    not is_responsible
                    and (state == "validate" and val_type == "hr")
                    and holiday.holiday_type == "employee"
                ):
                    raise UserError(
                        _(
                            "You must either be a Time off Officer or Time off Manager "
                            "to approve this leave"
                        )
                    )
