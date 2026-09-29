# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

SYNC_TRIGGER_FIELDS = {
    "work_location_id",
    "resource_calendar_id",
    "date_version",
    "active",
    "contract_date_start",
    "contract_date_end",
}


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.model_create_multi
    def create(self, vals_list):
        """Keep the public holidays in step with a new version.

        The work location and the working schedule live on the version, and
        contract flows create versions directly, without going through the
        employee. During the creation of the employee itself the version does
        not carry its employee yet, so this is a no-op there and the employee
        trigger covers it.
        """
        versions = super().create(vals_list)
        versions.sudo().employee_id._trigger_public_holiday_resync()
        return versions

    def write(self, vals):
        """Resync when a version write changes what somebody is entitled to.

        Writing a delegated field on the employee lands here too, so this is
        the single trigger for work location and schedule changes; a write
        done straight on the version -- the version form, a contract flow --
        bypasses ``hr.employee.write`` entirely and used to go stale until
        the nightly synchronisation. Every version's schedule is collected,
        before and after: the holidays of a period follow the contract valid
        then.
        """
        calendars = self.sudo().employee_id.version_ids.resource_calendar_id
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            calendars |= self.sudo().employee_id.version_ids.resource_calendar_id
            if calendars:
                calendars._trigger_public_holiday_sync()
        return res

    def unlink(self):
        # Removing a version can promote another one to being current.
        employees = self.sudo().employee_id
        res = super().unlink()
        employees.exists()._trigger_public_holiday_resync()
        return res
