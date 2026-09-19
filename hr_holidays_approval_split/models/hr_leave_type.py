from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    validation_type_split = fields.Selection(
        [
            ("both", "Hours and Days require approval"),
            ("hours", "Only Hours require approval"),
            ("days", "Only Days require approval"),
        ],
        string="Approval Type",
        default="both",
        help="""
            Define whether approval is required for hour-based requests,
            day-based requests or both.
        """,
    )
