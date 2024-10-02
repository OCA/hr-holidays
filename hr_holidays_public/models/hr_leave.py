# Copyright 2017-2021 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def action_validate(self):
        """Inject the needed context for excluding public holidays (if applicable) on
        the actions derived from this validation. This is required for example for
        `project_timesheet_holidays` for not generating the timesheet on the public
        holiday. Unfortunately, no regression test can be added, being in a separate
        module.
        """
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

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        if self.holiday_status_id.exclude_public_holidays or not self.holiday_status_id:
            instance = self.with_context(
                employee_id=self.employee_id.id, exclude_public_holidays=True
            )
        else:
            instance = self
        return super(HrLeave, instance)._get_durations(
            check_leave_type, resource_calendar
        )

    def _get_domain_from_get_unusual_days(self, date_from, date_to=None):
        domain = [("date", ">=", date_from)]
        # Use the employee of the user or the one who has the context
        employee_id = self.env.context.get("employee_id", False)
        employee = (
            self.env["hr.employee"].browse(employee_id)
            if employee_id
            else self.env.user.employee_id
        )
        if date_to:
            domain.append(
                (
                    "date",
                    "<",
                    date_to,
                )
            )
        country_id = employee.address_id.country_id.id
        if not country_id:
            country_id = self.env.company.country_id.id or False
        if country_id:
            domain.extend(
                [
                    "|",
                    ("year_id.country_id", "=", False),
                    ("year_id.country_id", "=", country_id),
                ]
            )
        state_id = employee.address_id.state_id.id
        if not state_id:
            state_id = self.env.company.state_id.id or False
        if state_id:
            domain.extend(
                [
                    "|",
                    ("state_ids", "in", [state_id]),
                    ("state_ids", "=", False),
                ]
            )
        return domain

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        res = super().get_unusual_days(date_from, date_to=date_to)
        domain = self._get_domain_from_get_unusual_days(
            date_from=date_from, date_to=date_to
        )
        public_holidays = self.env["hr.holidays.public.line"].search(domain)
        for public_holiday in public_holidays:
            res[fields.Date.to_string(public_holiday.date)] = True
        return res
