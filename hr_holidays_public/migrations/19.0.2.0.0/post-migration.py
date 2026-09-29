# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

from odoo.addons.hr_holidays_public.hooks import bootstrap_regions


def migrate(cr, version):
    # Public holidays follow the region of the employee from this version
    # on. Every work location gets a region of its own, named after it,
    # owned by its company and carrying the country of its address; the
    # public holidays that used to be scoped to states are then assigned to
    # the regions of the work locations lying in them, so that everybody
    # keeps their public holidays.
    env = api.Environment(cr, SUPERUSER_ID, {})
    bootstrap_regions(env)
