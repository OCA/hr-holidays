# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    country_id = fields.Many2one(
        comodel_name="res.country",
        compute="_compute_country_id",
    )
    state_ids = fields.Many2many(
        comodel_name="res.country.state",
        domain="[('country_id', '=', country_id)]",
        string="States",
        help="States for which this leave is applicable",
    )

    @api.depends("company_id")
    def _compute_country_id(self):
        for item in self:
            if not item.resource_id:
                item.country_id = item.company_id.country_id
            else:
                item.country_id = self.env["res.country"]
