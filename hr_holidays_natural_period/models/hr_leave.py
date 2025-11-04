# Copyright 2020-2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.misc import frozendict


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_number_of_days(self, date_from, date_to, employee_id):
        natural_period = bool(
            self.holiday_status_id.request_unit
            in ("natural_day", "natural_day_half_day")
        )
        new_context = frozendict(self.env.context, natural_period=natural_period)
        self.env.context = new_context
        return super(HrLeave, self)._get_number_of_days(date_from, date_to, employee_id)
