# Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    restrict_dates = fields.Boolean(
        string="Restrict",
        help="Check this if you want to forbid requesting "
        "leaves outside this range, otherwise it will just "
        "display a warning to the user.",
    )


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    warning_validity = fields.Char(compute="_compute_warning_range")
    restrict_dates = fields.Boolean(
        string="Restrict dates", related="holiday_status_id.restrict_dates"
    )

    @api.depends("holiday_status_id", "date_from", "date_to")
    def _compute_warning_range(self):
        for record in self:
            try:
                record.with_context(
                    compute_warning_range=True
                )._check_leave_type_validity()
            except ValidationError as e:
                record.warning_validity = e.args[0]
            else:
                record.warning_validity = False

    @api.constrains("holiday_status_id", "date_to", "date_from")
    def _check_leave_type_validity(self):
        if not self.env.context.get("compute_warning_range", False):
            self = self.filtered("restrict_dates")
        super(HolidaysRequest, self)._check_leave_type_validity()
