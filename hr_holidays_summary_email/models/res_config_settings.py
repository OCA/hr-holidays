# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_holidays_summary_weekly_dow = fields.Selection(
        related="company_id.hr_holidays_summary_weekly_dow",
        readonly=False,
        required=True,
    )
