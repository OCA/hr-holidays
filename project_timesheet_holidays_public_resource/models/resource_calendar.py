# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _update_public_holiday_timesheets(self):
        """Refresh the future public holiday timesheets after the days changed.

        The timesheet of a public holiday is a snapshot of the working hours
        at generation time. Standard refreshes it when an employee switches
        schedules, but not when the schedule itself changes: removing the
        Friday left every future Friday holiday timesheeted, and adding a day
        timesheeted nothing. The same standard delete-and-recreate cycle is
        run here for everybody on the schedule -- regeneration skips the days
        the schedule no longer works, because a holiday without working hours
        yields no timesheet line.

        Only the future is touched, like on a schedule switch: the past is
        accounting history.
        """
        if not self:
            return
        employees = (
            self.env["hr.employee"]
            .sudo()
            .search([("resource_calendar_id", "in", self.ids)])
        )
        employees._refresh_future_public_holiday_timesheets()
