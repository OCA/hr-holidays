# Copyright 2020-2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""Natural period: extend leave type with 'natural_day' request unit."""

from odoo import fields, models


class HrLeaveType(models.Model):
    """Extend leave type with 'natural_day' request unit."""

    _inherit = "hr.leave.type"

    request_unit = fields.Selection(
        selection_add=[("natural_day", "Natural day")],
        ondelete={"natural_day": "set default"},
    )
