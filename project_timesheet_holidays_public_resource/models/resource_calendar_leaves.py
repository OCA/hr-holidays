# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves._generate_public_holiday_resource_timesheets()
        return leaves

    @api.model
    def _prune_off_contract_public_holiday_timesheets(self, lines):
        """Drop generated public holiday entries on days no contract covers.

        A public holiday only concerns somebody employed on that day. Only
        entries stemming from a generated public holiday are judged --
        hand-made global time off keeps its standard behaviour.
        """
        off_contract = lines.filtered(
            lambda line: line.employee_id
            and line.global_leave_id.public_holiday_line_id
            and not line.employee_id.sudo()._is_in_contract(line.date)
        )
        if off_contract:
            off_contract.write({"global_leave_id": False})
            off_contract.unlink()
        return lines - off_contract

    def _timesheet_create_lines(self):
        # Company-wide public holidays skip the days outside a contract.
        return self._prune_off_contract_public_holiday_timesheets(
            super()._timesheet_create_lines()
        )

    def _generate_public_time_off_timesheets(self, employees):
        # An archived employee can never receive a timesheet -- standard
        # raises instead of skipping, so they are left out up front.
        lines = super()._generate_public_time_off_timesheets(
            employees.filtered("active")
        )
        return self._prune_off_contract_public_holiday_timesheets(lines)

    def _generate_public_holiday_resource_timesheets(self):
        """Timesheet the public holidays that belong to one person.

        ``project_timesheet_holidays`` only timesheets company-wide time off
        on creation -- ``_generate_timesheeets`` keeps ``not resource_id`` --
        so a regional public holiday, which is generated for a single
        resource, produced nothing. Its generation for given employees,
        ``_generate_public_time_off_timesheets``, reads the attendances per
        resource already, so the personal records are handed to it for their
        person: the entries come out indistinguishable from the nationwide
        ones, and whatever else hooks on that generation applies to them too.

        A record is left out when one of its days is already accounted for;
        a public holiday spans a single day, so this is the day check it was.
        """
        lines = self.env["account.analytic.line"].sudo()
        candidates = self.sudo().filtered(
            lambda leave: leave.resource_id
            and leave.public_holiday_line_id
            and leave.company_id.internal_project_id
            and leave.company_id.leave_timesheet_task_id
        )
        if not candidates:
            return lines
        employees = (
            self.env["hr.employee"]
            .sudo()
            .search(
                [
                    ("resource_id", "in", candidates.resource_id.ids),
                    ("active", "=", True),
                ]
            )
        )
        employee_by_resource = {
            employee.resource_id.id: employee for employee in employees
        }
        # The days standard is going to book, looked up the way it does.
        work_days = candidates._work_time_per_day()
        to_book = defaultdict(lambda: self.env["resource.calendar.leaves"].sudo())
        for leave in candidates:
            employee = employee_by_resource.get(leave.resource_id.id)
            if not employee:
                continue
            calendar = leave.calendar_id or employee.resource_calendar_id
            days = [
                day for day, _hours in work_days.get(calendar.id, {}).get(leave.id, [])
            ]
            if not days or any(
                leave._public_holiday_day_already_accounted(employee, day)
                for day in days
            ):
                continue
            to_book[employee] |= leave
        for employee, leaves in to_book.items():
            lines |= leaves._generate_public_time_off_timesheets(employee)
        return lines

    def _public_holiday_day_already_accounted(self, employee, day):
        """Whether a leave or a public holiday timesheets that day already.

        The timesheets are what counts, not the leave itself: an approved
        leave still spans a public holiday appearing inside it, but its
        entry for that day is regenerated away, and the day then has to be
        booked as the public holiday it is.
        """
        self.ensure_one()
        return bool(
            self.env["account.analytic.line"]
            .sudo()
            .search_count(
                [
                    ("employee_id", "=", employee.id),
                    ("date", "=", day),
                    "|",
                    ("holiday_id", "!=", False),
                    ("global_leave_id", "!=", False),
                ],
                limit=1,
            )
        )

    def _get_personal_public_holidays(self):
        return self.filtered(
            lambda leave: leave.resource_id and leave.public_holiday_line_id
        )

    def _get_personal_overlapping_hr_leaves(self):
        """The approved leaves of the people these personal records are for."""
        overlapping = self.env["hr.leave"]
        for leave in self._get_personal_public_holidays():
            overlapping |= leave._get_overlapping_hr_leaves(
                [("employee_id.resource_id", "=", leave.resource_id.id)]
            )
        return overlapping

    def _get_timesheet_overlapping_leaves(self):
        """Also the leaves of the people the personal records are for."""
        overlapping = super()._get_timesheet_overlapping_leaves()
        if overlapping is None:
            return None
        return overlapping | self._get_personal_overlapping_hr_leaves()

    def _adapt_overlapping_leave_timesheets(self, previous=None):
        """Book the day of a personal public holiday for its person.

        ``calendar_public_holiday_resource`` re-timesheets the leaves a
        public holiday falls into; the personal ones are part of that lookup
        here. What remains is the entry of the public holiday itself, which
        standard only generates for company-wide records: after a creation
        it is skipped for somebody on leave, and after a move it was deleted
        along with the old day.
        """
        res = super()._adapt_overlapping_leave_timesheets(previous)
        personal = self._get_personal_public_holidays()
        if personal:
            personal.sudo()._generate_public_holiday_resource_timesheets()
        return res

    @api.ondelete(at_uninstall=False)
    def _regenerate_hr_leave_timesheets_on_personal_public_holiday_unlinked(self):
        """Give the leave its entry for the day back, as standard does."""
        overlapping = self._get_personal_overlapping_hr_leaves()
        if overlapping:
            overlapping.sudo()._generate_timesheets(
                ignored_resource_calendar_leaves=self._get_personal_public_holidays().ids
            )
