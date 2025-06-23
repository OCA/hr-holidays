# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class User(models.Model):
    _inherit = "res.users"

    def _compute_im_status(self):
        res = super()._compute_im_status()
        for user in self.filtered(
            lambda x: x.employee_id.is_public_holiday and "leave_" not in x.im_status
        ):
            user.im_status = user.employee_id._get_im_status_hr_holidays_public(
                user.im_status
            )
        return res
