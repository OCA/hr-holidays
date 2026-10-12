# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    hr_leave_summary_type = fields.Selection(
        related="employee_id.hr_leave_summary_type", readonly=False, related_sudo=False
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["hr_leave_summary_type"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["hr_leave_summary_type"]
