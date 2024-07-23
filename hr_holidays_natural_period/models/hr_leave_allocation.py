# Copyright 2024 APSL-Nagarro - Antoni Marroig Campomar
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    # Added option to this field because it is now computed (was related before).
    type_request_unit = fields.Selection(
        selection_add=[("natural_day", "Natural day")],
    )
