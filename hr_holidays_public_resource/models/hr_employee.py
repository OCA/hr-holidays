# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models

# Work location and working schedule live on `hr.version` and trigger there;
# a write on the employee's delegated fields lands in `hr.version.write` too.
SYNC_TRIGGER_FIELDS = {
    "active",
    "company_id",
}


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        employees._trigger_public_holiday_resync()
        return employees

    def write(self, vals):
        # A move between schedules changes both of them.
        calendars = self.resource_calendar_id
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            (calendars | self.resource_calendar_id)._trigger_public_holiday_sync()
        return res

    def _trigger_public_holiday_resync(self):
        """Regenerate the public holidays of the schedules these people use.

        Hiring someone, moving them to another schedule or changing where
        they work changes what has to exist. Every version's schedule is
        synchronised, not just the current one: the holidays of a period
        follow the contract valid then, so a version dated in the future
        already moves the days it covers.
        """
        calendars = self.sudo().version_ids.resource_calendar_id
        if calendars:
            calendars._trigger_public_holiday_sync()

    def _get_own_public_holiday_leaves(self, date_from, date_to):
        """The public holidays generated for this person in particular."""
        self.ensure_one()
        if not self.resource_id:
            return self.env["resource.calendar.leaves"]
        return (
            self.env["resource.calendar.leaves"]
            .sudo()
            .search(
                [
                    ("resource_id", "=", self.resource_id.id),
                    ("public_holiday_line_id", "!=", False),
                    ("date_from", "<=", date_to),
                    ("date_to", ">=", date_from),
                ]
            )
        )

    def _get_unusual_days(self, date_from, date_to=None):
        """Grey out the public holidays this person in particular is given.

        Standard reads the working time of the schedule without anybody on it,
        so a regional public holiday, which belongs to one resource, is invisible
        there. A calendar shown for an employee has to use their own days.
        """
        res = super()._get_unusual_days(date_from, date_to)
        if not self:
            return res
        self.ensure_one()
        start = self._parse_unusual_days_datetime(date_from)
        end = self._parse_unusual_days_datetime(date_to or date_from)
        for leave in self._get_own_public_holiday_leaves(start, end):
            day = leave.public_holiday_line_id.date
            key = fields.Date.to_string(day)
            if key in res:
                res[key] = True
        return res

    @api.model
    def _parse_unusual_days_datetime(self, value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
