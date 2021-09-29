# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_number_of_days(self, date_from, date_to, employee_id):
        if self.holiday_status_id.exclude_public_holidays or not self.holiday_status_id:
            instance = self.with_context(
                employee_id=employee_id, exclude_public_holidays=True
            )
        else:
            instance = self
        return super(HrLeave, instance)._get_number_of_days(
            date_from, date_to, employee_id
        )

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        res = super().get_unusual_days(date_from, date_to=date_to)
        domain = [("date", ">=", date_from)]
        if date_to:
            domain.append(
                (
                    "date",
                    "<",
                    date_to,
                )
            )
        country_id = self.env.user.employee_id.address_id.country_id.id
        if not country_id:
            country_id = self.env.company.country_id.id or False
        if country_id:
            domain.extend(
                [
                    "|",
                    ("year_id.country_id", "=", False),
                    ("year_id.country_id", "=", country_id),
                ]
            )
        state_id = self.env.user.employee_id.address_id.state_id.id
        if not state_id:
            country_id = self.env.company.state_id.id or False
        if state_id:
            domain.extend(
                [
                    "|",
                    ("state_ids", "in", [state_id]),
                    ("state_ids", "=", False),
                ]
            )

        public_holidays = self.env["hr.holidays.public.line"].search(domain)
        for public_holiday in public_holidays:
            res[fields.Date.to_string(public_holiday.date)] = True
        return res
