# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.osv import expression


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    def _domain_holiday_status_id(self):
        res = super(HolidaysAllocation, self)._domain_holiday_status_id()
        return expression.OR([[("allow_credit", "=", True)], res])

    holiday_status_id = fields.Many2one(
        "hr.leave.type", domain=_domain_holiday_status_id
    )
