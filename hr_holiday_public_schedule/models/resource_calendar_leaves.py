# Copyright 2026 Daniel Reis <dreis.pt@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    hr_holiday_schedule_id = fields.Many2one(
        "hr.holiday.schedule",
        string="Holiday Schedule",
        ondelete="set null",
        index=True,
    )
    hr_holiday_rule_id = fields.Many2one(
        "hr.holiday.schedule.rule",
        string="Holiday Rule",
        ondelete="set null",
    )
    hr_holiday_year = fields.Integer(string="Holiday Year")
