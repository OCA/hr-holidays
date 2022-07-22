# Copyright 2020-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_number_of_days(self, date_from, date_to, employee_id):
        instance = self.with_context(
            natural_period=bool(self.holiday_status_id.request_unit == "natural_day")
        )
        return super(HrLeave, instance)._get_number_of_days(
            date_from, date_to, employee_id
        )
