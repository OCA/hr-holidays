from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="Expiry Date")
    use_validity_dates = fields.Boolean()

    _sql_constraints = [
        (
            "date_check",
            "CHECK ( (use_validity_dates=FALSE) OR (date_start <= date_end))",
            "The start date must be anterior to the end date.",
        ),
    ]

    def write(self, vals):
        # find all allocations of same leave type and update validity dates
        if "date_start" in vals:
            allocations = self.env["hr.leave.allocation"].search(
                [("holiday_status_id", "in", self.ids)]
            )
            allocations.write({"date_from": vals.get("date_start", False)})
        if "date_end" in vals:
            allocations = self.env["hr.leave.allocation"].search(
                [("holiday_status_id", "in", self.ids)]
            )
            allocations.write({"date_to": vals.get("date_end", False)})
        return super().write(vals)
