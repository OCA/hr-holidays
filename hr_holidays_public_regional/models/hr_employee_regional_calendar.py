from odoo import fields, models


class EmployeeRegionalCalendar(models.Model):
    _name = "hr.employee.regional.calendar"
    _description = "Employee Regional Calendar"
    _order = "start_date desc"

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, ondelete="cascade"
    )
    calendar_id = fields.Many2one(
        "hr.holidays.public.regional",
        string="Regional Calendar",
        required=True,
        ondelete="restrict",
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
