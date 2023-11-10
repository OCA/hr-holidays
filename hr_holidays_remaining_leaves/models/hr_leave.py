import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)
from datetime import datetime

from odoo.tools.float_utils import float_round


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

        now = fields.Datetime.now()
        now = datetime.combine(now, datetime.min.time())

        for allocation in self:

            # Get all validated leaves filtered by employee and leave type
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", allocation.employee_id.id),
                    ("state", "=", "validate"),
                    ("holiday_status_id", "=", allocation.holiday_status_id.id),
                    "|",
                    ("holiday_allocation_id", "=", allocation.id),
                    ("holiday_allocation_id", "=", False),
                ]
            )

            # Set the remaining leaves
            allocation.remaining_leaves_hours = (
                allocation.number_of_hours_display
                - sum(leaves.mapped("number_of_hours_display"))
            )
            allocation.remaining_leaves_days = allocation.number_of_days - sum(
                leaves.mapped("number_of_days")
            )

            # Get past leaves
            past_leaves = leaves.filtered(lambda l: l.date_to < now)
            past_leave_hours = sum(past_leaves.mapped("number_of_hours_display"))
            past_leave_days = sum(past_leaves.mapped("number_of_days"))

            # Check for leaves that are active and calculate the exact number of hours and days
            active_leave_hours = 0
            active_leave_days = 0
            for leave in leaves.filtered(lambda l: l.date_from < now < l.date_to):
                result = self._get_number_of_days_and_hours(
                    leave.date_from, now, leave.employee_id.id
                )
                active_leave_days = result["days"]
                active_leave_hours = result["hours"]

            allocation.remaining_leaves_current_hours = (
                allocation.number_of_hours_display
                - past_leave_hours
                - active_leave_hours
            )
            allocation.remaining_leaves_current_days = (
                allocation.number_of_days - past_leave_days - active_leave_days
            )

    def _compute_remaining_leaves_display(self):
        for allocation in self:

            allocation.remaining_leaves_display = "%g %s" % (
                (
                    float_round(allocation.remaining_leaves_hours, precision_digits=2)
                    if allocation.type_request_unit == "hour"
                    else float_round(
                        allocation.remaining_leaves_days, precision_digits=2
                    )
                ),
                _("hours") if allocation.type_request_unit == "hour" else _("days"),
            )

            allocation.remaining_leaves_current_display = "%g %s" % (
                (
                    float_round(
                        allocation.remaining_leaves_current_hours, precision_digits=2
                    )
                    if allocation.type_request_unit == "hour"
                    else float_round(
                        allocation.remaining_leaves_current_days, precision_digits=2
                    )
                ),
                _("hours") if allocation.type_request_unit == "hour" else _("days"),
            )
