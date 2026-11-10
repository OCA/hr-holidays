# Copyright 2026 Creublanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class HrLeave(models.Model):

    _inherit = "hr.leave"

    def _action_user_cancel(self, reason):
        res = super()._action_user_cancel(reason)
        for leave in self:
            responsible = (
                leave.employee_id.leave_manager_id
                or leave.employee_id.parent_id.user_id
            )
            if responsible and responsible.partner_id:
                leave.message_post(
                    body=_(
                        "%(employee)s has canceled their time off from "
                        "%(date_from)s to %(date_to)s.\nReason: %(reason)s",
                        employee=leave.employee_id.name,
                        date_from=leave.date_from,
                        date_to=leave.date_to,
                        reason=reason,
                    ),
                    partner_ids=responsible.partner_id.ids,
                    subtype_xmlid="mail.mt_note",
                )
        return res
