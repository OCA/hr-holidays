# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    # On the version, like the work location and the working schedule: the
    # public holidays of a period follow the contract valid then. Delegated
    # onto the employee through `_inherits`, where it shows read-only: the
    # value follows the public holiday region of the work location, so
    # there is exactly one place to maintain the mapping.
    # Not stored: searches through the field delegate to the related path
    # automatically, and an unstored value can never go stale.
    public_holiday_region_id = fields.Many2one(
        "calendar.public.holiday.region",
        string="Public Holiday Region",
        related="work_location_id.public_holiday_region_id",
        help="The place of work whose public holidays this person gets, on "
        "top of the nationwide ones. Derived from the work location.",
    )
