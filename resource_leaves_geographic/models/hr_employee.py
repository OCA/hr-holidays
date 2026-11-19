# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_public_holidays(self, date_start, date_end):
        # Filter the records by country and state; there is no method in super() to
        # generate the domain and extend it
        res = super()._get_public_holidays(date_start, date_end)
        if self.address_id:
            res = res.filtered(
                lambda x: (
                    x.country_id == self.address_id.country_id
                    and (not x.state_ids or self.address_id.state_id in x.state_ids)
                )
            )
        return res

    def _get_unusual_days(self, date_from, date_to=None):
        # We include, for context, the address that we will use as a reference later
        # in _leave_intervals_batch()
        _self = self.with_context(employee_address_id=self.address_id.id)
        return super(HrEmployee, _self)._get_unusual_days(
            date_from=date_from, date_to=date_to
        )
