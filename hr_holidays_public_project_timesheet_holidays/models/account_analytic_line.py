# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    public_holiday_line_id = fields.Many2one(
        "calendar.public.holiday.line",
        string="Public Holiday",
        ondelete="set null",
        index="btree_not_null",
    )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_linked_leave(self):
        if any(line.public_holiday_line_id for line in self):
            raise UserError(
                self.env._(
                    "You cannot delete timesheets that are linked to public holidays."
                )
            )
        return super()._unlink_except_linked_leave()
