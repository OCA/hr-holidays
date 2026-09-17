# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from datetime import date

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError


class HRHolidaysPublicRegional(models.Model):
    _name = "hr.holidays.public.regional"
    _description = "Public Holidays Regional"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(required=True)
    display_name = fields.Char("Name", compute="_compute_display_name", store=True)
    line_ids = fields.One2many(
        "hr.holidays.public.regional.line", "calendar_id", "Regional Holidays Dates"
    )
    year = fields.Integer("Calendar Year", required=True, default=date.today().year)

    @api.depends("name", "year")
    def _compute_display_name(self):
        for line in self:
            line.display_name = f"{line.name} ({line.year})"

    @api.model
    @api.returns("hr.holidays.public.regional.line")
    def get_regional_holidays_list(
        self, employee, year=None, start_dt=None, end_dt=None
    ):
        """
        Returns recordset of hr.holidays.public.line
        for the current year and employee
        :param year: year as string (optional if start_dt and end_dt defined)
        :param start_dt: start_dt as date
        :param end_dt: end_dt as date
        :param employee_id: ID of the employee
        :return: recordset of hr.holidays.public.line
        """
        if not start_dt and not end_dt:
            year = year or datetime.date.today().year
            start_dt = datetime.date(year, 1, 1)
            end_dt = datetime.date(year, 12, 31)
        if employee:
            employee_regional_calendar_ids = self.env[
                "hr.employee.regional.calendar"
            ].search(
                [
                    ("employee_id", "=", employee.id),
                ]
            )
            employee_calendar_ids = (
                employee_regional_calendar_ids.mapped("calendar_id").ids
                if employee_regional_calendar_ids
                else []
            )

            if employee_calendar_ids:
                domain = [
                    ("date", ">=", start_dt),
                    ("date", "<=", end_dt),
                    ("calendar_id", "in", employee_calendar_ids),
                ]
                return self.env["hr.holidays.public.regional.line"].search(domain)
        return self.env["hr.holidays.public.regional.line"].browse()

    @api.model
    def is_public_regional_holiday(self, selected_date, employee):
        """
        Returns True if selected_date is a public holiday for the employee
        :param selected_date: datetime object
        :param employee_id: ID of the employee
        :return: bool
        """
        holidays_lines = self.get_regional_holidays_list(
            employee=employee, year=selected_date.year
        )
        if holidays_lines:
            hol_date = holidays_lines.filtered(lambda r: r.date == selected_date)
            if hol_date:
                return True
        return False


class HrHolidaysPublicRegionalLine(models.Model):
    _name = "hr.holidays.public.regional.line"
    _description = "Public Holidays Regional Lines"
    _order = "date, name desc"

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    calendar_id = fields.Many2one(
        "hr.holidays.public.regional",
        "Regional Calendar",
        required=True,
        ondelete="cascade",
    )
    meeting_id = fields.Many2one("calendar.event", string="Meeting", copy=False)

    @api.constrains("date")
    def _check_date_state(self):
        for line in self:
            if line.date.year != line.calendar_id.year:
                raise ValidationError(
                    _(
                        "Dates of holidays should be the same year as the calendar"
                        " year they are being assigned to"
                    )
                )

            if line.date and line.calendar_id:
                if line.calendar_id.line_ids.filtered_domain(
                    [("date", "=", line.date), ("id", "!=", line.id)]
                ):
                    raise ValidationError(
                        _("You can't create duplicate public holidays for the date %s.")
                        % line.date
                    )

    def _prepare_regional_holidays_meeting_values(self):
        self.ensure_one()
        categ_id = self.env.ref("hr_holidays_public_regional.event_type_holiday", False)
        meeting_values = {
            "name": (
                f"{self.name} ({self.calendar_id.name})"
                if self.calendar_id.name
                else self.name
            ),
            "start": self.date,
            "stop": self.date,
            "allday": True,
            "user_id": SUPERUSER_ID,
            "privacy": "confidential",
            "show_as": "busy",
        }
        if categ_id:
            meeting_values.update({"categ_ids": [(6, 0, categ_id.ids)]})
        return meeting_values

    @api.constrains("date", "name", "calendar_id")
    def _update_calendar_event(self):
        for rec in self:
            if rec.meeting_id:
                rec.meeting_id.write(rec._prepare_regional_holidays_meeting_values())

    @api.model
    def create(self, values):
        res = super().create(values)
        res.meeting_id = self.env["calendar.event"].create(
            res._prepare_regional_holidays_meeting_values()
        )
        return res

    def unlink(self):
        self.mapped("meeting_id").unlink()
        return super().unlink()
