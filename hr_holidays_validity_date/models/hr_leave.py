# Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
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
            # TODO: filter out the ones with allocation?
        # copied from the code before in Odoo standard
        # https://github.com/odoo/odoo/pull/96545/files
        for leave in self:
            vstart = leave.holiday_status_id.date_start
            vstop = leave.holiday_status_id.date_end
            dfrom = leave.date_from
            dto = leave.date_to
            if vstart and vstop:
                if dfrom and dto and (dfrom.date() < vstart or dto.date() > vstop):
                    raise ValidationError(
                        _(
                            "%(leave_type)s are only valid between %(start)s and %(end)s",
                            leave_type=leave.holiday_status_id.display_name,
                            start=vstart,
                            end=vstop,
                        )
                    )
            elif vstart:
                if dfrom and (dfrom.date() < vstart):
                    raise ValidationError(
                        _(
                            "%(leave_type)s are only valid starting from %(date)s",
                            leave_type=leave.holiday_status_id.display_name,
                            date=vstart,
                        )
                    )
            elif vstop:
                if dto and (dto.date() > vstop):
                    raise ValidationError(
                        _(
                            "%(leave_type)s are only valid until %(date)s",
                            leave_type=leave.holiday_status_id.display_name,
                            date=vstop,
                        )
                    )

    def action_validate(self):
        # Prevent to validate a leave request if it is not in the validity range
        for holiday in self:
            if holiday.warning_validity:
                raise ValidationError(holiday.warning_validity)
        return super().action_validate()
