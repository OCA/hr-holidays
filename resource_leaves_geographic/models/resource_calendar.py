# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from collections import defaultdict

from odoo import models

from odoo.addons.resource.models.resource import Intervals, make_aware


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _get_general_time_off_intervals_by_state(self, domain=None, any_calendar=False):
        """Get a map of State to Intervals of leaves for the given domain."""
        domain = domain or []
        # Respect the any_calendar option
        if not any_calendar:
            domain = [("calendar_id", "in", self.ids + [False])] + domain
        # Ensure that the leaves are not related to a specific resource
        domain = [("resource_id", "=", False)] + domain
        # Iterate all matching leaves
        state_interval_map = defaultdict(Intervals)
        for res_cal_leave in self.env["resource.calendar.leaves"].search(domain):
            dttf, _f = make_aware(res_cal_leave.date_from)
            dttt, _f = make_aware(res_cal_leave.date_to)
            # Add the interval to the corresponding State or False if no state
            if res_cal_leave.state_ids:
                for state in res_cal_leave.state_ids:
                    state_interval_map[state.id] |= Intervals(
                        [(dttf, dttt, res_cal_leave)]
                    )
            else:
                state_interval_map[False] |= Intervals([(dttf, dttt, res_cal_leave)])
        return state_interval_map

    def _leave_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None, any_calendar=False
    ):
        # All interval batches (with/out State)
        res = super()._leave_intervals_batch(
            start_dt,
            end_dt,
            resources=resources,
            domain=domain,
            tz=tz,
            any_calendar=any_calendar,
        )
        # Overwrite the result if resources are specified, but only with
        # the global leaves (skipping the local leaves) using the domain
        for resource in resources or []:
            res.update(
                super()._leave_intervals_batch(
                    start_dt,
                    end_dt,
                    resources=resource,
                    domain=[("state_ids", "=", False)],  # Force global leaves
                    tz=tz,
                    any_calendar=any_calendar,
                )
            )
        # Get Local interval batches by State
        state_interval_map = self._get_general_time_off_intervals_by_state(
            domain=domain, any_calendar=any_calendar
        )
        # Post-process generated intervals
        for resource_id in res.keys():
            if not resource_id:
                # If no resource is specified, only consider Global leaves
                res[resource_id] = state_interval_map[False]
            else:
                # If resource is specified, add Local Leaves to the result if
                # the State of its Work Address has Local leaves
                resource_state_id = (
                    self.env["hr.employee"]
                    .sudo()
                    .search([("resource_id", "=", resource_id)], limit=1)
                    .address_id.state_id.id
                )
                if resource_state_id in state_interval_map:
                    res[resource_id] |= state_interval_map[resource_state_id]
        return res
