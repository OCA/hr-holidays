# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    auto_extend_type = fields.Boolean(
        related="holiday_status_id.auto_extend", string="Auto extend type"
    )
    auto_extend = fields.Boolean(
        compute="_compute_auto_extend", store=True, readonly=False
    )
    auto_extend_period = fields.Integer(
        compute="_compute_auto_extend", store=True, readonly=False
    )

    def _check_date_state(self):
        if not self.env.context.get("__no_check_state_date"):
            super()._check_date_state()

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """Returns a float equals to the timedelta between two dates given as string.
        We need to modify in order to add the compute_leaves = False
        """
        if not self.env.context.get("__no_check_state_date") or not employee_id:
            return super()._get_number_of_days(date_from, date_to, employee_id)
        employee = self.env["hr.employee"].browse(employee_id)
        return employee._get_work_days_data_batch(
            date_from, date_to, compute_leaves=False
        )[employee.id]

    @api.depends("holiday_status_id")
    def _compute_auto_extend(self):
        for record in self:
            record.auto_extend = record.holiday_status_id.auto_extend
            record.auto_extend_period = record.holiday_status_id.auto_extend_period

    def _cron_auto_extend_domain(self):
        return [
            ("request_date_to", "<=", fields.Date.today()),
            ("auto_extend", "=", True),
            ("auto_extend_period", ">", 0),
            ("state", "=", "validate"),
        ]

    def _cron_auto_extend(self):
        leaves = self.search(self._cron_auto_extend_domain())
        for leave in leaves.with_context(__no_check_state_date=True):
            request_date_to = leave.request_date_to + timedelta(
                days=leave.auto_extend_period
            )
            domain = [
                ("date_from", "<", request_date_to),
                ("date_from", ">", leave.date_from),
                ("employee_id", "=", leave.employee_id.id),
                ("id", "!=", leave.id),
                ("state", "not in", ["cancel", "refuse"]),
            ]
            if self.search(domain, limit=1):
                leave.auto_extend = False
                leave.activity_schedule(
                    "hr_holidays_auto_extend.mail_activity_error_auto_extend",
                )
                continue
            vals = {"request_date_to": request_date_to}
            vals.update(
                leave.onchange(vals, ["request_date_to"], leave._onchange_spec())[
                    "value"
                ]
            )
            leave.write(vals)
            leave._remove_resource_leave()
            leave._create_resource_leave()
