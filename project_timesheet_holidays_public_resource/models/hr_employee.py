# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _create_future_public_holidays_timesheets(self, employees):
        """Also back-fill the public holidays that belong to one person.

        Standard walks ``resource_calendar_id.global_leave_ids`` and the
        company-wide time off, both of which are resource-less, so the regional
        public holidays generated for an employee were left out when they were
        hired, reactivated or moved to another working schedule.
        """
        res = super()._create_future_public_holidays_timesheets(employees)
        leaves = (
            self.env["resource.calendar.leaves"]
            .sudo()
            .search(
                [
                    ("resource_id", "in", employees.resource_id.ids),
                    ("public_holiday_line_id", "!=", False),
                    ("date_from", ">=", fields.Datetime.today()),
                ]
            )
        )
        if leaves:
            res |= leaves._generate_public_holiday_resource_timesheets()
        res = self.env[
            "resource.calendar.leaves"
        ]._prune_off_contract_public_holiday_timesheets(res)
        # Standard does not deduplicate against entries that already exist
        # either -- and a new hire is back-filled twice, once through the
        # version trigger and once through the standard employee hook.
        line_model = self.env["account.analytic.line"].sudo()
        repeated = res.filtered(
            lambda line: line.global_leave_id
            and line_model.search_count(
                [
                    ("id", "not in", res.ids),
                    ("employee_id", "=", line.employee_id.id),
                    ("date", "=", line.date),
                    ("global_leave_id", "=", line.global_leave_id.id),
                ],
                limit=1,
            )
        )
        if repeated:
            repeated.write({"global_leave_id": False})
            repeated.unlink()
            res -= repeated
        return res

    def _refresh_future_public_holiday_timesheets(self):
        """Rebuild the future public holiday timesheets from scratch.

        The standard delete-and-recreate cycle of a schedule switch, run per
        company and with the company selected -- the timesheet machinery
        refuses an employee outside ``env.companies``. The past stays as it
        was booked.
        """
        employees = self.filtered("active")
        for company in employees.company_id:
            company_employees = employees.filtered(
                lambda employee, company=company: employee.company_id == company
            ).with_context(allowed_company_ids=company.ids)
            company_employees._delete_future_public_holidays_timesheets()
            company_employees._create_future_public_holidays_timesheets(
                company_employees
            )
