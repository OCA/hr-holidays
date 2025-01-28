# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrHolidaysPublic(models.Model):
    _inherit = "hr.holidays.public"

    def _get_domain_states_filter(
        self, pholidays, start_dt, end_dt, employee_id=None, partner_id=None
    ):
        domain = super()._get_domain_states_filter(
            pholidays=pholidays,
            start_dt=start_dt,
            end_dt=end_dt,
            employee_id=employee_id,
            partner_id=partner_id,
        )
        # To check for holidays in work locations, we must use the employee's
        # information instead of the partner's information
        employee_id = employee_id or self.env.context.get("employee_id", False)
        employee = self.env["hr.employee"].browse(employee_id) if employee_id else False
        # We check if the employee has a work location set, and we add that
        # restriction to the domain
        if employee and employee.work_location_id:
            domain += [
                "|",
                ("work_location_ids", "=", False),
                ("work_location_ids", "=", employee.work_location_id.id),
            ]
        else:
            domain.append(("work_location_ids", "=", False))
        return domain


class HrHolidaysPublicLine(models.Model):
    _inherit = "hr.holidays.public.line"

    work_location_ids = fields.Many2many(
        "hr.work.location",
        "hr_holiday_public_work_location_rel",
        "line_id",
        "work_location_id",
        "Related Work Locations",
    )

    @api.constrains("work_location_ids")
    def _check_date_state_work_location_ids(self):
        self._check_date_state()

    @api.constrains("work_location_ids")
    def _update_calendar_event_work_location_ids(self):
        self._update_calendar_event()

    def _get_domain_check_date_state_one_state_ids(self):
        domain = super()._get_domain_check_date_state_one_state_ids()
        if self.work_location_ids:
            domain += [("work_location_ids", "!=", False)]
        return domain

    def _get_domain_check_date_state_one(self):
        domain = super()._get_domain_check_date_state_one()
        domain += [("work_location_ids", "=", False)]
        return domain

    def _prepare_holidays_meeting_values(self):
        res = super()._prepare_holidays_meeting_values()
        if self.work_location_ids:
            res["description"] += ": " + ", ".join(
                self.work_location_ids.mapped("name")
            )
        return res
