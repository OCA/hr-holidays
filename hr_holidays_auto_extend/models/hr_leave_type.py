# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    auto_extend = fields.Boolean()
    auto_extend_period = fields.Integer(default=7)
