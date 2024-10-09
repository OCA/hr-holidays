# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_round


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    allow_credit = fields.Boolean(
        help=(
            "If set to true, employees would be able to make requests for this"
            " leave type even if allocated amount is insufficient."
        ),
    )
    creditable_employee_ids = fields.Many2many(
        string="Creditable Employees",
        comodel_name="hr.employee",
        help="If set, limits credit allowance to specified employees",
    )
    creditable_employee_category_ids = fields.Many2many(
        string="Creditable Employee Tags",
        comodel_name="hr.employee.category",
        help=(
            "If set, limits credit allowance to employees with at least one of"
            " specified tags"
        ),
    )
    creditable_department_ids = fields.Many2many(
        string="Creditable Departments",
        comodel_name="hr.department",
        help="If set, limits credit allowance to employees of specified departments",
    )

    @api.onchange("requires_allocation", "allocation_validation_type")
    def _onchange_allow_credit(self):
        if self.requires_allocation == "no" or self.allocation_validation_type == "no":
            self.allow_credit = False

    def name_get(self):
        if not self.requested_name_get():
            return super().name_get()
        res = []
        for record in self:
            record_name = record.name
            extra = False
            if record.requires_allocation == "yes":
                if record.virtual_remaining_leaves >= 0:
                    extra = _("%g")
                    extra += (
                        _(" hours") if record.request_unit == "hour" else _(" days")
                    )
                    extra += _(" available")
                    if record.allow_credit:
                        extra += _(" + credit")
                    extra = extra % (
                        float_round(record.virtual_remaining_leaves, precision_digits=2)
                        or 0.0
                    )
                elif record.allow_credit:
                    extra = _("%g")
                    extra += (
                        _(" hours") if record.request_unit == "hour" else _(" days")
                    )
                    extra += _(" used in credit")
                    extra = extra % (
                        float_round(
                            -record.virtual_remaining_leaves, precision_digits=2
                        )
                        or 0.0
                    )
            if extra:
                record_name = _("%(name)s (%(extra)s)") % {
                    "name": record_name,
                    "extra": extra,
                }
            res.append((record.id, record_name))
        return res
