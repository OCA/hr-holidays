# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    exclude_public_regional_holidays = fields.Boolean(
        default=True,
        help=(
            "If enabled, public regional holidays are "
            "skipped in leave days calculation."
        ),
    )
