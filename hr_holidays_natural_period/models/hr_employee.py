# Copyright 2024 APSL-Nagarro - Antoni Marroig Campomar
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_consumed_leaves(self, leave_types, target_date=False, ignore_future=False):
        """We need to set request_unit as 'day' to avoid the calculations being done
        as hours.
        """
        old_request_unit_data = {}
        for item in leave_types.filtered(lambda x: x.request_unit == "natural_day"):
            old_request_unit_data[item.id] = item.request_unit
            item.sudo().request_unit = "day"
        res = super()._get_consumed_leaves(leave_types, target_date, ignore_future)
        for item in leave_types:
            if item.id in old_request_unit_data:
                item.sudo().request_unit = old_request_unit_data[item.id]
        return res
