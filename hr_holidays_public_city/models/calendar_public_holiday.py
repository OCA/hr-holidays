# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class ResourceCalendarPublicHoliday(models.Model):
    _inherit = "calendar.public.holiday"

    def _get_domain_states_filter(self, pholidays, start_dt, end_dt, partner_id=None):
        domain = super()._get_domain_states_filter(
            pholidays=pholidays, start_dt=start_dt, end_dt=end_dt, partner_id=partner_id
        )
        partner = partner_model = self.env["res.partner"]
        if partner_id:
            partner = partner_model.browse(partner_id)
        if partner and partner.city_id:
            domain += [
                "|",
                ("city_ids", "=", False),
                ("city_ids", "=", partner.city_id.id),
            ]
        else:
            domain.append(("city_ids", "=", False))
        return domain
