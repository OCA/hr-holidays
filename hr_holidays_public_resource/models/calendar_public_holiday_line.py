# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.fields import Domain


class CalendarPublicHolidayLine(models.Model):
    _inherit = "calendar.public.holiday.line"

    def _get_public_holiday_resource_targets(self, calendars):
        """Resolve region-scoped public holidays to the people they are for.

        A working schedule is one scope, so generating a scoped public
        holiday on it would give it to everybody sharing the schedule. It is
        generated for the resource of each employee assigned to one of its
        regions instead, which lets colleagues on one schedule keep
        different regions.

        The region follows the **work location** of the employee -- where
        the work is actually done, which is what a public holiday follows.
        Both the region and the schedule are taken from the version
        (contract) valid on the day of the line, so a contract change in
        October moves the October holidays without touching the March ones.
        A day no contract covers is given to nobody.
        """
        targets = super()._get_public_holiday_resource_targets(calendars)
        scoped = self.filtered(lambda line: line.active and line.region_ids)
        if not scoped:
            return targets
        # Matched through the versions rather than the current values, so a
        # region somebody works at only under a past or future contract is
        # found as well.
        employees = (
            self.env["hr.employee"]
            .sudo()
            .search(
                Domain("version_ids.resource_calendar_id", "in", calendars.ids)
                & Domain("resource_id", "!=", False)
                & Domain(
                    "version_ids.public_holiday_region_id",
                    "in",
                    scoped.region_ids.ids,
                )
            )
        )
        for employee in employees:
            company = employee.company_id
            if not company:
                continue
            for line in scoped:
                if not employee._is_in_contract(line.date):
                    continue
                version = employee._get_version(line.date)
                calendar = version.resource_calendar_id
                # A calendar outside the requested subset stays untouched by
                # this run and would collide with its existing mirror.
                if not calendar or calendar not in calendars:
                    continue
                region = version.public_holiday_region_id
                if region not in line.region_ids:
                    continue
                # The country of the region decides, not the company's.
                if not region._matches_public_holiday_country(line):
                    continue
                targets.append((line, employee.resource_id, calendar, company))
        return targets
