# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    state_ids = fields.Many2many(
        comodel_name="res.country.state",
        string="States",
        help="States for which this leave is applicable",
    )
