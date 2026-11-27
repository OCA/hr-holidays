# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _get_public_holidays_extra_domain(self, partner_id=None):
        """Return the domain for public holidays applicable to a work address.

        Holidays without address restrictions apply to everyone, while
        state-specific holidays only apply to addresses in the corresponding state.
        """
        partner = self.env["res.partner"].browse(partner_id)
        self.ensure_one()
        domain = [("state_ids", "=", False)]
        if partner and partner.state_id:
            domain = [("state_ids", "in", [False] + partner.state_id.ids)]
        return domain

    def _work_intervals_batch(
        self, start_dt, end_dt, resources_per_tz=None, domain=None, compute_leaves=True
    ):
        # When splitting a leave, apply the same restrictions used when calculating the
        # employee's public holiday intervals.
        if self.env.context.get("from_create_leaves_from_split"):
            domain += self._get_public_holidays_extra_domain(
                self.env.context.get("partner_id")
            )
        return super()._work_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources_per_tz=resources_per_tz,
            domain=domain,
            compute_leaves=compute_leaves,
        )

    def _leave_intervals_batch(
        self, start_dt, end_dt, resources_per_tz=None, domain=None
    ):
        # Apply restrictions to company holidays while preserving the default behavior
        # of considering only leaves counted as absences.
        extra_domain = self._get_public_holidays_extra_domain(
            self.env.context.get("partner_id")
        )
        if domain is None:
            # It's important to add the same domain that would be added in resource
            # if there is no domain, so that everything is consistent.
            domain = [("count_as", "=", "absence")] + extra_domain
        else:
            domain += extra_domain
        return super()._leave_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources_per_tz=resources_per_tz,
            domain=domain,
        )
