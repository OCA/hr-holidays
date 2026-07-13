# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    hr_leave_summary_type = fields.Selection(
        selection=[("no", "No"), ("daily", "Daily"), ("weekly", "Weekly")],
        string="Leave Summary Email",
        required=True,
        default="no",
    )
    last_hr_leave_summary_sent = fields.Date(
        string="Last Leave Summary Email Sent",
        readonly=True,
    )
