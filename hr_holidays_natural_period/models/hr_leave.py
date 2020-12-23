# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.onchange("holiday_status_id")
    def _onchange_holiday_status_id(self):
        res = super()._onchange_holiday_status_id()
        if (self._origin.holiday_status_id.request_unit == "natural_day") != (
            self.holiday_status_id.request_unit == "natural_day"
        ):
            self.with_context(natural_period=True)._onchange_leave_dates()
        return res

    def _get_number_of_days(self, date_from, date_to, employee_id):
        instance = self.with_context(
            natural_period=bool(self.holiday_status_id.request_unit == "natural_day")
        )
        return super(HrLeave, instance)._get_number_of_days(
            date_from, date_to, employee_id
        )
