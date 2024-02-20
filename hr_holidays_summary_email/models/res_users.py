# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    hr_leave_summary_type = fields.Selection(
        related="employee_id.hr_leave_summary_type", readonly=False, related_sudo=False
    )

    def __init__(self, pool, cr):
        """Override of __init__ to add access rights.
        Access rights are disabled by default, but allowed
        on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        super(ResUser, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = type(self).SELF_READABLE_FIELDS + [
            "hr_leave_summary_type"
        ]
        type(self).SELF_WRITEABLE_FIELDS = type(self).SELF_WRITEABLE_FIELDS + [
            "hr_leave_summary_type"
        ]
