# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

# Fields whose change moves which days an employee is entitled to, or under
# which working hours -- the future timesheets have to follow.
TIMESHEET_TRIGGER_FIELDS = {
    "work_location_id",
    "resource_calendar_id",
    "date_version",
    "contract_date_start",
    "contract_date_end",
    "active",
}


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.model_create_multi
    def create(self, vals_list):
        """Refresh the timesheets when a contract flow adds a version.

        During the creation of the employee itself the version does not
        carry its employee yet, so this is a no-op there; the standard
        new-hire back-fill covers that case.
        """
        versions = super().create(vals_list)
        versions.sudo().employee_id._refresh_future_public_holiday_timesheets()
        return versions

    def write(self, vals):
        """Rebuild the future timesheets when the contract scope changes.

        The public holiday mirrors are resynchronised first, through the
        ``hr_holidays_public_resource`` trigger below this one, so the
        timesheets are rebuilt from the already-updated mirrors. Ending a
        contract removes the future entries beyond its end; extending it
        brings them back.
        """
        employees = self.sudo().employee_id
        res = super().write(vals)
        if TIMESHEET_TRIGGER_FIELDS.intersection(vals):
            (
                employees | self.sudo().employee_id
            )._refresh_future_public_holiday_timesheets()
        return res

    def unlink(self):
        # Removing a version can promote another one to being current.
        employees = self.sudo().employee_id
        res = super().unlink()
        employees.exists()._refresh_future_public_holiday_timesheets()
        return res
