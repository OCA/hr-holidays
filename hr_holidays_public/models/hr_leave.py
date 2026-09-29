# Copyright 2017-2021 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _excludes_public_holidays(self):
        """Whether the public holidays are skipped in this leave's duration.

        Keyed on the standard *Ignore Public Holidays* setting of the leave
        type, so that the same checkbox rules whether the public holidays
        are taken out of the attendance intervals here or, with them
        materialised as global time off, left out by standard itself. A
        leave without a type yet skips them.
        """
        self.ensure_one()
        return (
            not self.holiday_status_id
            or not self.holiday_status_id.include_public_holidays_in_duration
        )

    def _action_validate(self, check_state=True):
        """Inject the needed context for excluding public holidays (if applicable) on
        the actions derived from this validation. This is required for example for
        `project_timesheet_holidays` for not generating the timesheet on the public
        holiday. Unfortunately, no regression test can be added, being in a separate
        module.
        """
        for leave in self:
            if leave._excludes_public_holidays():
                leave = leave.with_context(
                    employee_id=leave.employee_id.id, exclude_public_holidays=True
                )
            super(HrLeave, leave)._action_validate(check_state=check_state)
        return True

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        exclude_public_holidays_leaves = self.filtered(
            lambda x: x._excludes_public_holidays()
        )
        res = super(HrLeave, (self - exclude_public_holidays_leaves))._get_durations(
            check_leave_type=check_leave_type, resource_calendar=resource_calendar
        )
        for leave in exclude_public_holidays_leaves:
            leave = leave.with_context(
                employee_id=leave.employee_id.id, exclude_public_holidays=True
            )
            _res = super(HrLeave, leave)._get_durations(
                check_leave_type=check_leave_type, resource_calendar=resource_calendar
            )
            res[leave.id] = _res[leave.id]
        return res

    def _get_domain_from_get_unusual_days(self, date_from, date_to=None):
        """Domain of the public holiday lines applying to the employee.

        The region is the public holiday region of the employee, derived
        from their work location; the country is the one of that region,
        falling back to the work address of the employee and then to the
        company. A nationwide line always applies, a regional one only in
        the employee's region.
        """
        domain = [("date", ">=", date_from)]
        # Use the employee of the user or the one who has the context
        employee_id = self.env.context.get("employee_id", False)
        employee = (
            self.env["hr.employee"].browse(employee_id)
            if employee_id
            else self.env.user.employee_id
        )
        if date_to:
            domain.append(("date", "<=", date_to))
        region = employee.sudo().public_holiday_region_id
        country_id = region.country_id.id or employee.address_id.country_id.id
        if not country_id:
            country_id = self.env.company.country_id.id or False
        if country_id:
            domain.append(("public_holiday_id.country_id", "in", (False, country_id)))
        if region:
            domain.extend(
                [
                    "|",
                    ("region_ids", "in", region.ids),
                    ("region_ids", "=", False),
                ]
            )
        else:
            domain.append(("region_ids", "=", False))
        return domain

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        res = super().get_unusual_days(date_from=date_from, date_to=date_to)
        domain = self._get_domain_from_get_unusual_days(
            date_from=date_from, date_to=date_to
        )
        public_holidays = self.env["calendar.public.holiday.line"].search(domain)
        for public_holiday in public_holidays:
            res[fields.Date.to_string(public_holiday.date)] = True
        return res
