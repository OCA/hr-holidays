# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models

from odoo.addons.resource.models.utils import HOURS_PER_DAY


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    @api.depends("number_of_days", "holiday_status_id", "employee_id", "holiday_type")
    def _compute_number_of_hours_display(self):
        for allocation in self:
            allocation_calendar = (
                allocation.holiday_status_id.company_id.resource_calendar_id
            )
            if allocation.holiday_type == "employee" and allocation.employee_id:
                allocation_calendar = (
                    allocation.employee_id.sudo().resource_id.calendar_id
                )
            allocation.number_of_hours_display = allocation.number_of_days * (
                allocation_calendar.hours_per_day or HOURS_PER_DAY
            )
