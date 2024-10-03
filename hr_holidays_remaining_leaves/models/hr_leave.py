# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, fields, models
from odoo.tools.float_utils import float_round

from odoo.addons.resource.models.utils import HOURS_PER_DAY

_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    remaining_leaves_hours = fields.Float(compute="_compute_remaining_leaves")
    remaining_leaves_days = fields.Float(compute="_compute_remaining_leaves")
    remaining_leaves_display = fields.Char(
        "Remaining", compute="_compute_remaining_leaves_display"
    )
    remaining_leaves_current_hours = fields.Float(compute="_compute_remaining_leaves")
    remaining_leaves_current_days = fields.Float(compute="_compute_remaining_leaves")
    remaining_leaves_current_display = fields.Char(
        "Current Remaining", compute="_compute_remaining_leaves_display"
    )

    def _get_number_of_days_and_hours(self, date_from, date_to, employee_id):
        employee = self.env["hr.employee"].browse(employee_id)
        domain = [
            (
                "company_id",
                "in",
                self.env.company.ids + self.env.context.get("allowed_company_ids", []),
            )
        ]
        return employee._get_work_days_data_batch(
            date_from, date_to, domain=domain, compute_leaves=False
        )[employee.id]

    def _compute_remaining_leaves(self):
        all_consumed_leaves = self.employee_id._get_consumed_leaves(
            self.holiday_status_id
        )[0]
        all_consumed_leaves_current = self.employee_id._get_consumed_leaves(
            self.holiday_status_id, ignore_future=True
        )[0]
        for allocation in self:
            consumes_allo = all_consumed_leaves[allocation.employee_id][
                allocation.holiday_status_id
            ][allocation]
            consumes_allo_current = all_consumed_leaves_current[allocation.employee_id][
                allocation.holiday_status_id
            ][allocation]
            allocation_calendar = (
                allocation.holiday_status_id.company_id.resource_calendar_id
            )
            if allocation.holiday_type == "employee" and allocation.employee_id:
                allocation_calendar = allocation.employee_id.sudo().resource_calendar_id
            allocation.remaining_leaves_days = consumes_allo["remaining_leaves"]
            allocation.remaining_leaves_hours = consumes_allo["remaining_leaves"] * (
                allocation_calendar.hours_per_day or HOURS_PER_DAY
            )
            allocation.remaining_leaves_current_days = consumes_allo_current[
                "remaining_leaves"
            ]
            allocation.remaining_leaves_current_hours = consumes_allo_current[
                "remaining_leaves"
            ] * (allocation_calendar.hours_per_day or HOURS_PER_DAY)

    def _compute_remaining_leaves_display(self):
        for allocation in self:
            allocation.remaining_leaves_display = "{} {}".format(
                float_round(allocation.remaining_leaves_hours, precision_digits=2)
                if allocation.type_request_unit == "hour"
                else float_round(allocation.remaining_leaves_days, precision_digits=2),
                _("hours") if allocation.type_request_unit == "hour" else _("days"),
            )

            allocation.remaining_leaves_current_display = "{} {}".format(
                (
                    float_round(
                        allocation.remaining_leaves_current_hours,
                        precision_digits=2,
                    )
                    if allocation.type_request_unit == "hour"
                    else float_round(
                        allocation.remaining_leaves_current_days, precision_digits=2
                    )
                ),
                _("hours") if allocation.type_request_unit == "hour" else _("days"),
            )
