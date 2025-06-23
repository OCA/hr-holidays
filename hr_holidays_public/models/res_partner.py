# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_im_status(self):
        res = super()._compute_im_status()
        for item in self.filtered(
            lambda x: x.user_ids.employee_id.is_public_holiday
            and "leave_" not in x.im_status
        ):
            item.im_status = (
                item.user_ids.employee_id._get_im_status_hr_holidays_public(
                    item.im_status
                )
            )
        return res
