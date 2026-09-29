# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _get_public_holiday_employees(self):
        """Employees whose working time this schedule governs."""
        self.ensure_one()
        return self.env["hr.employee"].search([("resource_calendar_id", "=", self.id)])

    @api.depends("public_holiday_employee_sync")
    def _compute_public_holiday_overview_line_ids(self):
        """Also count the scoped days the schedule's employees get.

        The nationwide reach comes from ``calendar_public_holiday_resource``;
        a region-scoped public holiday reaches the schedule through the
        people on it, which only this module can resolve. The employee
        entries are gated by *Apply Employee Public Holidays*, so a schedule
        opting out keeps the nationwide overview only.
        """
        res = super()._compute_public_holiday_overview_line_ids()
        line_model = self.env["calendar.public.holiday.line"]
        for calendar in self.filtered("public_holiday_employee_sync"):
            employees = calendar.sudo()._get_public_holiday_employees()
            regions = employees.public_holiday_region_id
            if not regions:
                continue
            weekdays = calendar._public_holiday_overview_weekdays()
            # The country of the region decides, not the one of the
            # schedule's company; the working days of the schedule still do.
            scoped = line_model.search([("region_ids", "in", regions.ids)]).filtered(
                lambda line, regions=regions, weekdays=weekdays: (
                    weekdays is None or line.date.weekday() in weekdays
                )
                and any(
                    region._matches_public_holiday_country(line)
                    for region in regions & line.region_ids
                )
            )
            calendar.public_holiday_overview_line_ids |= scoped
        return res

    def _public_holidays_excluded_from_attendances(self):
        """The generated time off is what standard excludes; not the engine.

        ``hr_holidays_public`` takes public holidays out of the attendance
        intervals itself. Here every public holiday exists as global time
        off, which standard already leaves out of the working time, so the
        second engine is switched off; both key on the standard *Ignore
        Public Holidays* setting of the leave type, so nothing changes for
        the user.
        """
        return False
