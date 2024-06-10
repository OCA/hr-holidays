# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    request_time_hour_from = fields.Float("Float hour from")

    request_hour_from = fields.Char(compute="_compute_hour_from", store=True)

    request_time_hour_to = fields.Float("Float hour to")

    request_hour_to = fields.Char(compute="_compute_hour_to", store=True)

    @api.depends("request_time_hour_from")
    def _compute_hour_from(self):
        for leave in self:
            leave.request_hour_from = "%.2f" % self.request_time_hour_from

    @api.depends("request_time_hour_to")
    def _compute_hour_to(self):
        for leave in self:
            leave.request_hour_to = "%.2f" % self.request_time_hour_to

    @api.depends("request_time_hour_from", "request_time_hour_to")
    def _compute_date_from_to(self):
        return super()._compute_date_from_to()

    def action_validate(self):
        """fixed action_validate() override from hr_holidays_public"""
        for leave in self:
            if (
                leave.holiday_status_id.exclude_public_holidays
                or not leave.holiday_status_id
            ):
                leave = leave.with_context(
                    employee_id=leave.employee_id.id, exclude_public_holidays=True
                )
            super(HrLeave, leave).action_validate()
        return True
