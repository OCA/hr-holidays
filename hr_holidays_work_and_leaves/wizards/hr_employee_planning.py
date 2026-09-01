# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrEmployeePlanning(models.TransientModel):
    _name = "hr.employee.planning"
    _description = "Employee Planning"

    employee_id = fields.Many2one("hr.employee", required=True, readonly=True)
    date_start = fields.Date(required=True, default=fields.Date.today)
    date_end = fields.Date(
        required=True,
        default=lambda self: date.today().replace(day=1)
        + relativedelta(months=1, days=-1),
    )
    planning_line_ids = fields.One2many(
        "hr.employee.planning.line", "planning_id", readonly=True
    )

    def action_compute(self):
        self.planning_line_ids.unlink()
        start_datetime = datetime.combine(self.date_start, time.min)
        end_datetime = datetime.combine(self.date_end, time.max)
        days = self.employee_id._get_full_schedule_per_day(start_datetime, end_datetime)
        self.env["hr.employee.planning.line"].create(
            [
                {
                    "planning_id": self.id,
                    "date": day.date,
                    "hours_work": day.hours_work,
                    "hours_leave": day.hours_leave,
                    "hours_holiday": day.hours_holiday,
                    "hours_leave_requested": day.hours_leave_requested,
                    "hours_appointment": day.hours_appointment,
                }
                for day in days
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee.planning",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class HrEmployeePlanningLine(models.TransientModel):
    _name = "hr.employee.planning.line"
    _description = "Employee Planning Line"
    _order = "date"

    planning_id = fields.Many2one("hr.employee.planning")
    date = fields.Date()
    hours_work = fields.Float(digits=(6, 2))
    hours_leave = fields.Float(digits=(6, 2))
    hours_holiday = fields.Float(digits=(6, 2))
    hours_leave_requested = fields.Float(digits=(6, 2))
    hours_appointment = fields.Float(digits=(6, 2))
