# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models
from odoo.tools import groupby


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _prepare_holidays_meeting_values(self):
        """Set calendar events privacy for hr leaves according to type"""
        res = super()._prepare_holidays_meeting_values()
        for user, holidays in groupby(self, lambda h: h.user_id):
            for holiday, meeting_vals in zip(holidays, res.get(user.id)):
                meeting_vals[
                    "privacy"
                ] = holiday.holiday_status_id.calendar_event_privacy
        return res
