# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def action_validate(self):
        """Inject the needed context for excluding public holidays
        (if applicable) on the actions derived from this validation.
        This is required for example for `project_timesheet_holidays`
        for not generating the timesheet on the public holiday.
        Unfortunately, no regression test can be added, being in a separate module."""
        for leave in self:
            if (
                leave.holiday_status_id.exclude_public_regional_holidays
                or not leave.holiday_status_id
            ):
                leave = self.with_context(
                    employee_id=leave.employee_id.id,
                    exclude_public_regional_holidays=True,
                )
            super(HrLeave, leave).action_validate()
        return True

    def _get_duration(self, check_leave_type=True, resource_calendar=None):
        if (
            self.holiday_status_id.exclude_public_regional_holidays
            or not self.holiday_status_id
        ):
            instance = self.with_context(exclude_public_regional_holidays=True)
        else:
            instance = self
        return super(HrLeave, instance)._get_duration(
            check_leave_type, resource_calendar
        )

    @api.depends("number_of_days")
    def _compute_number_of_hours_display(self):
        to_serialize = self.filtered(
            lambda x: x.state == "validate"
            and x.holiday_status_id.exclude_public_regional_holidays
        )
        for leave in to_serialize:
            leave = leave.with_context(
                exclude_public_regional_holidays=True, employee_id=leave.employee_id.id
            )
            super(HrLeave, leave)._compute_number_of_hours_display()
        return super(HrLeave, self - to_serialize)._compute_number_of_hours_display()

    def _get_domain_from_get_unusual_days_regional(self, date_from, date_to=None):
        domain = [("date", ">=", date_from)]
        # Use the employee of the user or the one who has the context
        employee_id = self.env.context.get("employee_id", False)
        employee = (
            self.env["hr.employee"].browse(employee_id)
            if employee_id
            else self.env.user.employee_id
        )
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
        domain = [
            ("date", ">=", date_from),
            ("calendar_id", "in", employee_calendar_ids),
        ]
        if date_to:
            domain.append(
                (
                    "date",
                    "<=",
                    date_to,
                )
            )
        return domain

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        res = super().get_unusual_days(date_from, date_to=date_to)
        domain = self._get_domain_from_get_unusual_days_regional(
            date_from=date_from, date_to=date_to
        )
        public_regional_holidays = self.env["hr.holidays.public.regional.line"].search(
            domain
        )
        for public_regional_holiday in public_regional_holidays:
            res[fields.Date.to_string(public_regional_holiday.date)] = True
        return res
