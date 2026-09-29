# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.resource.models.resource_resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _public_holidays_excluded_from_attendances(self):
        """Whether public holidays are taken out of the attendance intervals.

        This is how the leave durations skip public holidays without any
        time off record existing for them. A module materialising the
        public holidays as global time off -- which standard then excludes
        on its own -- switches this engine off, so that the two never apply
        at once.
        """
        return True

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources, tz
    ):
        employee_id = self.env.context.get("employee_id", False)
        if not employee_id:
            return intervals
        # Read with elevated rights: the employee record may not be readable
        # to the user requesting the leave. The public employee model is not
        # used on purpose -- it is a SQL view, which is stale while an
        # upgrade is still loading the modules that contribute columns to
        # it, and the leave re-evaluation runs this engine from there.
        employee = self.env["hr.employee"].sudo().browse(employee_id)
        region = employee.public_holiday_region_id
        list_by_dates = (
            self.env["calendar.public.holiday"]
            .get_holidays_list(
                start_dt=start_dt.date(),
                end_dt=end_dt.date(),
                partner_id=employee.address_id.id,
                region_ids=region.ids,
                # The country of the region decides; the work address only
                # stands in for an employee without one.
                country_id=region.country_id.id,
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
        if (
            self.env.context.get("exclude_public_holidays")
            and resources
            and self._public_holidays_excluded_from_attendances()
        ):
            return self._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, res, resources, tz
            )
        return res
