# Copyright 2024 APSL-Nagarro - Antoni Marroig Campomar
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""Natural period: extend allocation with 'Natural day' request unit."""

from odoo import fields, models


class HrLeaveAllocation(models.Model):
    """Extend allocation to support natural day request unit."""

    _inherit = "hr.leave.allocation"

    # Added option to this field because it is now computed (was related before).
    type_request_unit = fields.Selection(
        selection_add=[("natural_day", "Natural day")],
    )
