# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    leave_manager_ids = fields.Many2many(
        'res.users',
        string='Time Off',
        compute='_compute_leave_manager',
        store=True,
        readonly=False,
        help='Select the users responsible for approving "Time Off" of this employee.\n'
        'If empty, the approval is done by an Administrator or Approver (determined in settings/users).',
    )

    def create(self, values):
        res = super().create(values)
        return res

    def write(self, values):
        res = super().write(values)
        return res
