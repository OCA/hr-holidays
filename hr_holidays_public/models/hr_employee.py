# Copyright 2024 Tecnativa - David Vidal
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_public_holiday_lines(self, date_start, date_end):
        """Just get the employees holidays"""
        domain = self.env["hr.leave"]._get_domain_from_get_unusual_days(
            date_from=date_start, date_to=date_end
        )
        return self.env["calendar.public.holiday.line"].search(domain)

    @api.model
    def get_public_holidays_data(self, date_start, date_end):
        # Include public holidays in the calendar summary
        res = super().get_public_holidays_data(date_start=date_start, date_end=date_end)
        self = self._get_contextual_employee()
        public_holidays = self._get_public_holiday_lines(date_start, date_end).sorted(
            "date"
        )
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

    is_public_holiday = fields.Boolean(
        string="Public Holiday Today", compute="_compute_is_public_holiday"
    )

    def _compute_is_public_holiday(self):
        holiday_public = self.env["calendar.public.holiday"]
        for item in self:
            item.is_public_holiday = holiday_public.is_public_holiday(
                fields.Date.context_today(item), partner_id=item.address_id.id
            )

    def _get_im_status_hr_holidays_public(self, key):
        im_status_mapped = {
            "online": "leave_online",
            "away": "leave_away",
            "offline": "leave_offline",
        }
        return im_status_mapped[key]

    def _compute_leave_status(self):
        res = super()._compute_leave_status()
        for item in self.filtered(lambda x: not x.is_absent and x.is_public_holiday):
            item.is_absent = True
        return res
