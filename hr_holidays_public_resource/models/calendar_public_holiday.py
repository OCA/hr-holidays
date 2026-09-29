# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CalendarPublicHoliday(models.Model):
    _inherit = "calendar.public.holiday"

    employee_count = fields.Integer(compute="_compute_employee_count")

    def _get_applicable_employees(self):
        """Employees these public holidays actually give a day off.

        Nationwide public holidays are generated company-wide and so reach
        everybody working in a matching company; scoped ones are generated
        for the resource of each employee at one of the regions. Both are
        counted, the way the synchronisation resolves them.
        """
        self.ensure_one()
        Employee = self.env["hr.employee"]
        employees = Employee
        calendars = self._get_applicable_resource_calendars()
        if calendars:
            employees |= Employee.search(
                [("resource_calendar_id", "in", calendars.ids)]
            )
        syncing = (
            self.env["calendar.public.holiday.line"]
            ._get_public_holiday_calendars()
            .filtered("public_holiday_employee_sync")
        )
        targets = self.line_ids._get_public_holiday_resource_targets(syncing)
        resources = {resource.id for _line, resource, _cal, _company in targets}
        if resources:
            employees |= Employee.search([("resource_id", "in", list(resources))])
        return employees

    @api.depends(
        "country_id",
        "line_ids",
        "line_ids.region_ids",
        "line_ids.active",
    )
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(record._get_applicable_employees())

    def action_view_employees(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Employees"),
            "res_model": "hr.employee",
            "view_mode": "list,form",
            "domain": [("id", "in", self._get_applicable_employees().ids)],
        }
