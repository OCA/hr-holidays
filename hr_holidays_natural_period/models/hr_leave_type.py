# Copyright 2020-2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    request_unit = fields.Selection(
        selection_add=[("natural_day", "Natural day")],
        ondelete={"natural_day": "set default"},
    )
