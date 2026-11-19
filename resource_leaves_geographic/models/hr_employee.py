# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_public_holidays(self, date_start, date_end):
        """Return public holidays applicable to the employee's work address."""
        res = super()._get_public_holidays(date_start, date_end)
        # The parent method does not expose a domain hook, so filter the returned
        # holidays using the employee's address.
        return res.filtered_domain(
            self.resource_calendar_id._get_public_holidays_extra_domain(
                self.address_id.id
            )
        )

    def _get_unusual_days(self, date_from, date_to=None):
        # Pass the employee's address so calendar leave intervals can apply the
        # corresponding restrictions.
        _self = self.with_context(partner_id=self.address_id.id)
        return super(HrEmployee, _self)._get_unusual_days(
            date_from=date_from, date_to=date_to
        )

    def _list_work_time_per_day(
        self, from_datetime, to_datetime, calendar=None, domain=None
    ):
        # Provide the employee's work address to the calendar interval computation.
        calendar = calendar.with_context(partner_id=self.address_id.id)
        return super()._list_work_time_per_day(
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            calendar=calendar,
            domain=domain,
        )
