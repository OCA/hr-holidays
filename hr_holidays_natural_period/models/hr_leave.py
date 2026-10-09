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
        old_request_unit = self.holiday_status_id.request_unit
        is_request_unit_natural_day = is_mod_leave_type or (
            self.holiday_status_id.request_unit
            in ("natural_day", "natural_day_half_day")
        )
        instance = self.with_context(
            natural_period=is_request_unit_natural_day,
            old_request_unit=old_request_unit,
        )
        if is_request_unit_natural_day and not is_mod_leave_type:
            new_request_unit = (
                "half_day" if old_request_unit == "natural_day_half_day" else "day"
            )
            # HACK: The field is updated in this way to prevent recomputations.
            self.env.cache.update_raw(
                self.holiday_status_id,
                self.holiday_status_id._fields["request_unit"],
                [new_request_unit],
                dirty=True,
            )
        res = super(HrLeave, instance)._get_duration(
            check_leave_type=check_leave_type, resource_calendar=resource_calendar
        )
        if is_request_unit_natural_day and not is_mod_leave_type:
            self.env.cache.update_raw(
                self.holiday_status_id,
                self.holiday_status_id._fields["request_unit"],
                [old_request_unit],
                dirty=True,
            )
        return res
