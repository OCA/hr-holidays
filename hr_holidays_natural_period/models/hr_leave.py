# Copyright 2020-2024 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# Copyright 2025 Grupo Isonor - Alexandre D. Díaz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_duration(self, check_leave_type=True, resource_calendar=None):
        # We need to set request_unit as 'day'
        # to avoid the calculations being done as hours.
        mod_holidays_status_ids = self.env.context.get("mod_holidays_status_ids", [])
        is_mod_leave_type = self.holiday_status_id.id in mod_holidays_status_ids
        is_request_unit_natural_day = is_mod_leave_type or (
            self.holiday_status_id.request_unit == "natural_day"
        )
        instance = self.with_context(natural_period=is_request_unit_natural_day)
        if is_request_unit_natural_day:
            self.holiday_status_id.sudo().request_unit = "day"
        res = super(HrLeave, instance)._get_duration(
            check_leave_type=check_leave_type, resource_calendar=resource_calendar
        )
        if is_request_unit_natural_day:
            self.holiday_status_id.sudo().request_unit = "natural_day"
        return res
