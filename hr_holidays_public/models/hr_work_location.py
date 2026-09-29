# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrWorkLocation(models.Model):
    _inherit = "hr.work.location"

    public_holiday_region_id = fields.Many2one(
        "calendar.public.holiday.region",
        string="Public Holiday Region",
        help="The public holiday region standing for this work location. "
        "Everybody working here follows it: the assignment on the employee "
        "is derived from the work location of each version (contract). "
        "Installing the module builds one region per work location, owned "
        "by its company and carrying the country of its address.",
    )
