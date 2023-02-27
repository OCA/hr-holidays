# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    calendar_event_privacy = fields.Selection(
        [
            ("public", "Public"),
            ("private", "Private"),
            ("confidential", "Only internal users"),
        ],
        default="confidential",
        help="Defines privacy of calendar events created for this Time Off Type",
    )
