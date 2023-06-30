# Copyright 2020-2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    request_unit = fields.Selection(
        selection_add=[("natural_day", "Natural day")],
        ondelete={"natural_day": "set default"},
    )

    def _get_employees_days_per_allocation(self, employee_ids, date=None):
        """We need to set request_unit as 'day' to avoid the calculations being done
        as hours.
        Related code:
        hr_holidays/models/hr_leave_type.py#L313
        hr_holidays/models/hr_leave_type.py#L367
        """
        old_request_unit_data = {}
        for item in self.filtered(lambda x: x.request_unit == "natural_day"):
            old_request_unit_data[item.id] = item.request_unit
            item.sudo().request_unit = "day"
        res = super()._get_employees_days_per_allocation(
            employee_ids=employee_ids, date=date
        )
        for item in self:
            if item.id in old_request_unit_data:
                item.sudo().request_unit = old_request_unit_data[item.id]
        return res
