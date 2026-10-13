# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_missing_public_holiday_timesheets(self):
        if not self:
            return

        min_date = min(self.mapped("date_from")).date()
        max_date = max(self.mapped("date_to")).date()
        holiday_lines = self.env["calendar.public.holiday.line"].search(
            [
                ("date", ">=", min_date),
                ("date", "<=", max_date),
            ]
        )
        holiday_lines._generate_public_holiday_timesheets(
            self.employee_id,
            skip_validated_leave_check=True,
        )

    def action_refuse(self):
        result = super().action_refuse()
        self._check_missing_public_holiday_timesheets()
        return result

    def _action_user_cancel(self, reason=None):
        result = super()._action_user_cancel(reason)
        self._check_missing_public_holiday_timesheets()
        return result
