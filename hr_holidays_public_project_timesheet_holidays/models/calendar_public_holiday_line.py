# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import datetime, time

import pytz

from odoo import api, fields, models
from odoo.fields import Domain


class CalendarPublicHolidayLine(models.Model):
    _inherit = "calendar.public.holiday.line"

    def _get_holidays_lines_by_partner(self, partner_ids, start_dt, end_dt):
        holiday_api = self.env["calendar.public.holiday"]
        return {
            partner_id: holiday_api.get_holidays_list(
                start_dt=start_dt,
                end_dt=end_dt,
                partner_id=partner_id,
            )
            for partner_id in partner_ids
        }

    def _prepare_public_holiday_timesheet_vals(self, employee, work_hours_count):
        project = employee.company_id.internal_project_id
        task = employee.company_id.leave_timesheet_task_id
        return {
            "name": self.env._("Time Off"),
            "project_id": project.id,
            "task_id": task.id,
            "account_id": project.account_id.id,
            "unit_amount": work_hours_count,
            "user_id": employee.user_id.id,
            "date": self.date,
            "employee_id": employee.id,
            "company_id": employee.company_id.id,
            "public_holiday_line_id": self.id,
        }

    def _get_applicable_employees(self, employees, holidays_by_partner=None):
        self.ensure_one()
        if not employees:
            return self.env["hr.employee"]

        employees = employees.filtered("address_id")
        if not employees:
            return employees

        employees_by_partner = defaultdict(lambda: self.env["hr.employee"])
        for employee in employees:
            employees_by_partner[employee.address_id.id] |= employee

        holidays_by_partner = holidays_by_partner or {}
        missing_partners = [
            partner_id
            for partner_id in employees_by_partner
            if partner_id not in holidays_by_partner
        ]
        if missing_partners:
            holidays_by_partner.update(
                self._get_holidays_lines_by_partner(
                    missing_partners,
                    start_dt=self.date,
                    end_dt=self.date,
                )
            )

        applicable_employees = self.env["hr.employee"]
        for partner_id, partner_employees in employees_by_partner.items():
            partner_lines = holidays_by_partner[partner_id]
            if self in partner_lines:
                applicable_employees |= partner_employees
        return applicable_employees

    def _get_work_hours_per_employee(self, employees):
        self.ensure_one()
        work_hours_per_employee = {}
        employees_by_calendar = defaultdict(lambda: self.env["hr.employee"])
        for employee in employees:
            if not employee.resource_calendar_id:
                continue
            employees_by_calendar[employee.resource_calendar_id] |= employee

        for calendar, calendar_employees in employees_by_calendar.items():
            calendar_tz = pytz.timezone(calendar.tz)
            day_start = calendar_tz.localize(datetime.combine(self.date, time.min))
            day_end = calendar_tz.localize(datetime.combine(self.date, time.max))
            intervals = calendar._attendance_intervals_batch(
                day_start.astimezone(pytz.utc),
                day_end.astimezone(pytz.utc),
                resources=calendar_employees.resource_id,
                tz=calendar_tz,
            )
            for employee in calendar_employees:
                employee_intervals = intervals.get(employee.resource_id.id, [])
                work_hours_per_employee[employee.id] = sum(
                    (date_to - date_from).total_seconds() / 3600
                    for date_from, date_to, _dummy in employee_intervals
                )

        return work_hours_per_employee

    def _get_validated_leave_days_per_employee(self, employees):
        leave_days_per_employee = defaultdict(list)
        if not employees:
            return leave_days_per_employee
        domain = (
            Domain("employee_id", "in", employees.ids)
            & Domain("state", "=", "validate")
            & Domain("date_from", "<=", self.date)
            & Domain("date_to", ">=", self.date)
        )
        leaves_read_group = self.env["hr.leave"]._read_group(
            domain,
            ["employee_id"],
            ["date_from:array_agg", "date_to:array_agg"],
        )
        for employee, date_from_list, date_to_list in leaves_read_group:
            leave_days_per_employee[employee.id] = [
                (date_from.date(), date_to.date())
                for date_from, date_to in zip(
                    date_from_list, date_to_list, strict=False
                )
            ]
        return leave_days_per_employee

    def _get_existing_timesheet_employee_ids(self, employees):
        domain = (
            Domain("employee_id", "in", employees.ids)
            & Domain("date", "=", self.date)
            & (
                Domain("public_holiday_line_id", "=", self.id)
                | Domain("global_leave_id", "!=", False)
            )
        )
        existing_read_group = self.env["account.analytic.line"]._read_group(
            domain,
            ["employee_id"],
            ["__count"],
        )
        return {employee.id for employee, _count in existing_read_group}

    def _generate_public_holiday_timesheets(
        self, employees, skip_validated_leave_check=False
    ):
        vals_list = []
        today = fields.Date.today()
        holidays_by_partner = {}
        for holiday_line in self.filtered(
            lambda line: line.date and line.date >= today
        ):
            applicable_employees = holiday_line._get_applicable_employees(
                employees,
                holidays_by_partner=holidays_by_partner,
            )
            applicable_employees = applicable_employees.filtered(
                lambda employee: employee.active
                and employee.company_id.internal_project_id
                and employee.company_id.leave_timesheet_task_id
            )
            if not applicable_employees:
                continue

            leave_days_per_employee = defaultdict(list)
            if not skip_validated_leave_check:
                leave_days_per_employee = (
                    holiday_line._get_validated_leave_days_per_employee(
                        applicable_employees
                    )
                )
            existing_timesheet_employee_ids = (
                holiday_line._get_existing_timesheet_employee_ids(applicable_employees)
            )
            work_hours_per_employee = holiday_line._get_work_hours_per_employee(
                applicable_employees
            )

            for employee in applicable_employees:
                if employee.id in existing_timesheet_employee_ids:
                    continue

                if not skip_validated_leave_check:
                    employee_leave_days = leave_days_per_employee.get(employee.id, [])
                    if any(
                        date_from <= holiday_line.date <= date_to
                        for date_from, date_to in employee_leave_days
                    ):
                        continue

                work_hours = work_hours_per_employee.get(employee.id, 0)
                if not work_hours:
                    continue

                vals_list.append(
                    holiday_line._prepare_public_holiday_timesheet_vals(
                        employee,
                        work_hours,
                    )
                )

        return self.env["account.analytic.line"].sudo().create(vals_list)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        employees = self.env["hr.employee"].search(
            Domain("active", "=", True) & Domain("address_id", "!=", False)
        )
        records._generate_public_holiday_timesheets(employees)
        return records

    def write(self, vals):
        should_regenerate = False
        changed_lines = self.env["calendar.public.holiday.line"]
        if "date" in vals:
            target_date = fields.Date.to_date(vals["date"]) if vals["date"] else False
            changed_lines = self.filtered(lambda line: line.date != target_date)
            should_regenerate = bool(changed_lines)

        if should_regenerate:
            old_timesheets = (
                self.env["account.analytic.line"]
                .sudo()
                .search(
                    Domain("public_holiday_line_id", "in", changed_lines.ids)
                    & Domain("date", ">=", fields.Date.today())
                )
            )
            old_timesheets.write({"public_holiday_line_id": False})
            old_timesheets.unlink()

        result = super().write(vals)

        if should_regenerate:
            employees = self.env["hr.employee"].search(
                Domain("active", "=", True) & Domain("address_id", "!=", False)
            )
            changed_lines._generate_public_holiday_timesheets(employees)

        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_future_public_holiday_timesheets(self):
        timesheets = (
            self.env["account.analytic.line"]
            .sudo()
            .search(
                Domain("public_holiday_line_id", "in", self.ids)
                & Domain("date", ">=", fields.Date.today())
            )
        )
        timesheets.write({"public_holiday_line_id": False})
        timesheets.unlink()
