# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import Command, api, fields, models


class ResourceCalendarPublicHolidayWizardLine(models.TransientModel):
    _inherit = 'load.public.holiday.wizard.line'

    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Country",
        compute="_compute_country_id",
        store=True,
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
            item.country_id = item.company_id.country_id

    def _prepare_leave_values(self):
        values = super()._prepare_leave_values()
        values.update({
            "country_id": self.country_id.id,
            "state_ids": [Command.set(self.state_ids.ids)]
        })
        return values
