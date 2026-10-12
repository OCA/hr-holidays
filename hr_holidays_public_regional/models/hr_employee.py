# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import api, fields, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    def _get_public_regional_holiday_lines(self, date_start, date_end):
        """Just get the employees holidays"""
        domain = self.env["hr.leave"]._get_domain_from_get_unusual_days_regional(
            date_from=date_start, date_to=date_end
        )
        return self.env["hr.holidays.public.regional.line"].search(domain)

    @api.model
    def get_public_holidays_data(self, date_start, date_end):
        # Include public holidays in the calendar summary
        res = super().get_public_holidays_data(date_start, date_end)
        self = self._get_contextual_employee()
        public_holidays = self._get_public_regional_holiday_lines(
            date_start, date_end
        ).sorted("date")
        res += list(
            map(
                lambda bh: {
                    "id": -bh.id,
                    "colorIndex": 0,
                    "end": (datetime.combine(bh.date, datetime.max.time())).isoformat(),
                    "endType": "datetime",
                    "isAllDay": True,
                    "start": (
                        datetime.combine(bh.date, datetime.min.time())
                    ).isoformat(),
                    "startType": "datetime",
                    "title": bh.name,
                },
                public_holidays,
            )
        )
        return sorted(res, key=lambda x: x["start"])


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    regional_holiday_calendar_ids = fields.One2many(
        "hr.employee.regional.calendar", "employee_id", string="Regional Calendars"
    )
    is_public_regional_holiday = fields.Boolean(
        string="Public Holiday Today", compute="_compute_is_public_regional_holiday"
    )

    def _compute_is_public_regional_holiday(self):
        holiday_public_regional = self.env["hr.holidays.public.regional"]
        for item in self:
            item.is_public_regional_holiday = (
                holiday_public_regional.is_public_regional_holiday(
                    fields.Date.context_today(item), employee=item
                )
            )

    def _get_im_status_hr_holidays_public_regional(self, key):
        im_status_mapped = {
            "online": "leave_online",
            "away": "leave_away",
            "offline": "leave_offline",
        }
        return im_status_mapped[key]

    def _compute_leave_status(self):
        res = super()._compute_leave_status()
        for item in self.filtered(
            lambda x: not x.is_absent and x.is_public_regional_holiday
        ):
            item.is_absent = True
        return res
