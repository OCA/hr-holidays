from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    leave_validation_type = fields.Selection(
        selection_add=[
            ("tier_validation", "Use Tier Validation System"),
        ]
    )
