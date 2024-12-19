# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import api, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_public_holiday_lines(self, date_start, date_end):
        """Just get the employees holidays"""
        domain = self.env["hr.leave"]._get_domain_from_get_unusual_days(
            date_from=date_start, date_to=date_end
        )
        return self.env["hr.holidays.public.line"].search(domain)

    @api.model
    def get_public_holidays_data(self, date_start, date_end):
        # Include public holidays in the calendar summary
        res = super().get_public_holidays_data(date_start, date_end)
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
