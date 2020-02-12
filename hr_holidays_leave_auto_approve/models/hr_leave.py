# Copyright 2016-2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_approval_update(self, state):
        if self.env.user._is_admin():
            return
        return super()._check_approval_update(state)

    def _should_auto_approve(self):
        self.ensure_one()
        policy = self.holiday_status_id.auto_approve_policy
        return (self.can_approve and policy == "hr") or policy == "all"

    def _apply_auto_approve_policy(self):
        self.filtered(lambda r: r._should_auto_approve()).sudo().action_approve()

    @api.model
    def create(self, values):
        auto_approve = self._get_auto_approve_on_creation(values)
        tracking_disable = self.env.context.get("tracking_disable")
        mail_skip = self.env.context.get("mail_activity_automation_skip")
        ctx = self.env.context.copy()
        ctx.update(
            {
                "tracking_disable": tracking_disable or auto_approve,
                "mail_activity_automation_skip": mail_skip or auto_approve,
            }
        )
        res = super(HrLeave, self.with_context(ctx)).create(values)
        res._apply_auto_approve_policy()
        return res

    @api.model
    def _get_auto_approve_on_creation(self, values):
        auto_approve = False
        if values.get("holiday_status_id"):
            leave_type = self.env["hr.leave.type"].browse(
                values.get("holiday_status_id")
            )
            auto_approve = leave_type.auto_approve_policy != "no"
        return auto_approve
