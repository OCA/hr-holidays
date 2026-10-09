# Copyright 2024 APSL-Nagarro - Antoni Marroig Campomar
# Copyright 2025 Grupo Isonor - Alexandre D. Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_consumed_leaves(self, leave_types, target_date=False, ignore_future=False):
        """We need to set request_unit as 'day' to avoid the calculations being done
        as hours.
        """
        mod_leave_type_ids = self.env["hr.leave.type"]
        leave_types_data = {}
        for item in leave_types:
            if item.request_unit in ("natural_day", "natural_day_half_day"):
                leave_types_data[item] = item.request_unit
                new_request_unit = (
                    "half_day" if item.request_unit == "natural_day_half_day" else "day"
                )
                # HACK: The field is updated in this way to prevent recomputations
                self.env.cache.update_raw(
                    item,
                    item._fields["request_unit"],
                    [new_request_unit],
                    dirty=True,
                )
                mod_leave_type_ids |= item
        self = self.with_context(mod_holidays_status_ids=mod_leave_type_ids.ids)
        res = super()._get_consumed_leaves(leave_types, target_date, ignore_future)
        for item in mod_leave_type_ids:
            self.env.cache.update_raw(
                item,
                item._fields["request_unit"],
                [leave_types_data[item]],
                dirty=True,
            )
        return res
