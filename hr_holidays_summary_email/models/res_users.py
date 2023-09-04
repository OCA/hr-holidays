# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    hr_leave_summary_type = fields.Selection(
        related="employee_id.hr_leave_summary_type", readonly=False, related_sudo=False
    )
