# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.resource.models.resource_resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources, tz
    ):
        list_by_dates = (
            self.env["hr.holidays.public"]
            .get_holidays_list(
                start_dt=start_dt.date(),
                end_dt=end_dt.date(),
                employee_id=self.env.context.get("employee_id", False),
            )
            .mapped("date")
        )
        for resource in resources:
            interval_resource = intervals[resource.id]
            attendances = []
            for attendance in interval_resource._items:
                if attendance[0].date() not in list_by_dates:
                    attendances.append(attendance)
            intervals[resource.id] = Intervals(attendances)
        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources=resources,
            domain=domain,
            tz=tz,
            lunch=lunch,
        )
        if self.env.context.get("exclude_public_holidays") and resources:
            return self._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, res, resources, tz
            )
        return res
