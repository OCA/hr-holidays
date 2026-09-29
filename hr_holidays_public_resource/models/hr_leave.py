# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from pytz import utc

from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        """Grey out weekends and public holidays even without an employee.

        ``res.users.employee_id`` is company dependent, so an administrator
        looking at the time off dashboard with a company they have no employee
        record in falls back to an empty employee. Standard
        ``hr.employee._get_unusual_days`` then finds no contract version and
        reports *every* day as unusual, which shows the whole calendar as free
        and hides the public holidays this module exists to display.

        The company working schedule is the sensible stand-in there: it is what
        the company works by, and it carries the generated public holidays.
        """
        employee_id = self.env.context.get("employee_id", False)
        employee = (
            self.env["hr.employee"].browse(employee_id)
            if employee_id
            else self.env.user.employee_id
        )
        if employee:
            return super().get_unusual_days(date_from, date_to)
        calendar = self.env.company.resource_calendar_id
        if not calendar:
            return super().get_unusual_days(date_from, date_to)
        return calendar.sudo(False)._get_unusual_days(
            self._parse_unusual_days_datetime(date_from),
            self._parse_unusual_days_datetime(date_to or date_from),
            self.env.company,
        )

    @api.model
    def _parse_unusual_days_datetime(self, value):
        """Parse the datetime strings ``get_unusual_days`` is called with."""
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=utc)
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=utc)

    # ------------------------------------------------------------------
    # Mail silence under the synchronisation
    # ------------------------------------------------------------------
    # Maintaining a public holiday re-evaluates the leaves it overlaps, and
    # standard treats every consequence like a change somebody made by hand:
    # it emails the employee about days given back or taken, and a refusal
    # notifies the employee and the manager. Nobody acted, so nobody is
    # emailed -- the explanations stay in the chatter as plain notes.

    def _notify_change(self, message, subtype_xmlid="mail.mt_note"):
        if not self.env.context.get("public_holiday_sync"):
            return super()._notify_change(message, subtype_xmlid=subtype_xmlid)
        for leave in self:
            leave.message_post(body=message, subtype_xmlid=subtype_xmlid)
        return None

    def message_notify(self, **kwargs):
        if self.env.context.get("public_holiday_sync"):
            return self.env["mail.message"]
        return super().message_notify(**kwargs)

    def message_post(self, **kwargs):
        if self.env.context.get("public_holiday_sync"):
            kwargs.pop("partner_ids", None)
        return super().message_post(**kwargs)
