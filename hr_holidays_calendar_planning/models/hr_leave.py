# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_hour_from_to(self, request_date_from, request_date_to, day_period=None):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        self = self.with_context(
            flexible_hours_from_date=request_date_from,
            flexible_hours_to_date=request_date_to,
        )
        return super()._get_hour_from_to(request_date_from, request_date_to, day_period)

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        result = {}
        for leave in self:
            # It is important to define the appropriate context keys so that the value
            # is as expected.
            _leave = leave.with_context(
                flexible_hours_from_date=leave.request_date_from,
                flexible_hours_to_date=leave.request_date_to,
            )
            # TODO: Try to remove the call to that compute in
            # hr_employee_calendar_planning
            _leave.employee_id.sudo()._compute_is_flexible()
            result[leave.id] = super(HrLeave, _leave)._get_durations(
                check_leave_type=check_leave_type, resource_calendar=resource_calendar
            )[leave.id]
        return result
