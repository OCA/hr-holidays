# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.resource.models.resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources, tz
    ):
        holidays_by_country = {
            False: set(
                self.env["hr.holidays.public"]
                .get_holidays_list(
                    start_dt=start_dt.date(),
                    end_dt=end_dt.date(),
                    employee_id=self.env.context.get("employee_id", False),
                )
                .mapped("date")
            )
        }
        if resources:
            employees = self.env["hr.employee.public"].search(
                [("resource_id", "in", resources.ids)]
            )
            resource_country = {}
            for employee in employees:
                country = employee.address_id.country_id
                resource_country[employee.resource_id.id] = country.id
                if country.id not in holidays_by_country:
                    holidays_by_country[country.id] = set(
                        self.env["hr.holidays.public"]
                        .get_holidays_list(
                            start_dt=start_dt.date(),
                            end_dt=end_dt.date(),
                            employee_id=employee.id,
                        )
                        .mapped("date")
                    )
        # even if employees and resource_country are empty
        # we still process holidays, so provide defaults
        for resource in resources:
            interval_resource = intervals.get(
                resource.id, Intervals(self.env["hr.attendance"])
            )
            attendances = []
            country = resource_country.get(resource.id, self.env["res.country"])
            holidays = holidays_by_country.get(country, set())
            for attendance in interval_resource._items:
                if attendance[0].date() not in holidays:
                    attendances.append(attendance)
            intervals[resource.id] = Intervals(attendances)
        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt, end_dt=end_dt, resources=resources, domain=domain, tz=tz
        )
        if self.env.context.get("exclude_public_holidays") and resources:
            return self._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, res, resources, tz
            )
        return res
