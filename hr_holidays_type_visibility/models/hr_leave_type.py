# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    def _get_calendar_visibility(self):
        return [
            ("positive", _("Positive")),
            ("never", _("Never")),
            ("always", _("Always")),
        ]

    visible_calendar = fields.Selection(
        "_get_calendar_visibility",
        string="Visiblility Calendar",
        default="positive",
        required=True,
        help="Configure the visibility in the calendar dashboard header depending on "
        "the remaining leaves\n"
        "  * Positive: Show only if the total is positive. This is the Odoo default\n"
        "  * Never: Never show the total\n"
        "  * Always: Always show the total",
    )

    @api.model
    def get_days_all_request(self):
        leave_types = super().get_days_all_request()

        domain = [("visible_calendar", "=", "never")]
        exclude = self.search(domain).ids
        leave_types = [lt for lt in leave_types if lt[3] not in exclude]

        ids = [lt[3] for lt in leave_types]
        domain = [("visible_calendar", "=", "always"), ("id", "not in", ids)]
        leave_types.extend(lt._get_days_request() for lt in self.search(domain))
        return leave_types
