# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HolidaysPublicNextYearWizard(models.TransientModel):
    _name = "public.regional.holidays.wizard"
    _description = "Creates public regional holidays from existing ones"

    template_ids = fields.Many2many(
        comodel_name="hr.holidays.public.regional", string="Templates", required=True
    )
    year = fields.Integer(
        help="Year for which you want to create the public regional holidays. ",
        default=lambda self: fields.Date.today().year + 1,
        required=True,
    )

    def create_public_regional_holidays(self):
        self.ensure_one()

        ph_env = self.env["hr.holidays.public.regional"]
        phs = ph_env.search([("id", "in", self.template_ids.ids)])

        new_ph_ids = []
        for ph in phs:
            new_ph = ph.copy()
            new_ph.year = self.year

            new_ph_ids.append(new_ph.id)

            for last_ph_line in ph.line_ids:
                feb_29 = last_ph_line.date.month == 2 and last_ph_line.date.day == 29

                if feb_29:
                    # Handling this rare case would mean quite a lot of
                    # complexity because previous or next day might also be a
                    # public holiday.
                    raise UserError(
                        _(
                            "You cannot use as template the public regional holidays "
                            "of a year that "
                            "includes public regional holidays on 29th of February "
                            "(2016, 2020...), please select a template from "
                            "another year."
                        )
                    )

                new_date = last_ph_line.date.replace(year=self.year)

                new_ph_line_vals = {"date": new_date, "calendar_id": new_ph.id}
                last_ph_line.copy(new_ph_line_vals)

        domain = [["id", "in", new_ph_ids]]

        action = {
            "type": "ir.actions.act_window",
            "name": _("New public regional holidays"),
            "view_mode": "tree,form",
            "res_model": "hr.holidays.public.regional",
            "domain": domain,
        }

        return action
