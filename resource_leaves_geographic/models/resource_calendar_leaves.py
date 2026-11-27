# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models
from odoo.osv import expression


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    state_ids = fields.Many2many(
        comodel_name="res.country.state",
        string="States",
        help="States for which this leave is applicable",
    )

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        # When computing leave durations, only the leaves without State or
        # with the employee's State apply (see ``hr.leave._get_durations``)
        if "resource_leaves_geographic_state_id" not in self.env.context:
            return super()._search(domain, offset=offset, limit=limit, order=order)
        state_id = self.env.context["resource_leaves_geographic_state_id"]
        state_domain = [("state_ids", "=", False)]
        if state_id:
            state_domain = expression.OR(
                [state_domain, [("state_ids", "in", [state_id])]]
            )
        domain = expression.AND([domain, state_domain])
        return super()._search(domain, offset=offset, limit=limit, order=order)
