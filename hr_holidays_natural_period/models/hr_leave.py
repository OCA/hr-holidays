# Copyright 2020-2025 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# Copyright 2025 Grupo Isonor - Alexandre D. Díaz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        # We need to set request_unit as 'day'
        # to avoid the calculations being done as hours.
        mod_holidays_status_ids = self.env.context.get("mod_holidays_status_ids", [])
        natural_day_instances = self.filtered(
            lambda x: x.holiday_status_id.id in mod_holidays_status_ids
            or x.holiday_status_id.request_unit == "natural_day"
        )
        natural_day_instances.holiday_status_id.sudo().request_unit = "day"
        res = super(HrLeave, (self - natural_day_instances))._get_durations(
            check_leave_type=check_leave_type, resource_calendar=resource_calendar
        )
        if not natural_day_instances:
            return res
        _res = super(
            HrLeave, natural_day_instances.with_context(natural_period=True)
        )._get_durations(
            check_leave_type=check_leave_type, resource_calendar=resource_calendar
        )
        for item in natural_day_instances:
            res[item.id] = _res[item.id]
        natural_day_instances.holiday_status_id.sudo().request_unit = "natural_day"
        return res
