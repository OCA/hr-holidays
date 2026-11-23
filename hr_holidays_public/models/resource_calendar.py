# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.intervals import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources
    ):
        employee_id = self.env.context.get("employee_id", False)
        if not employee_id:
            return intervals
        employee = self.env["hr.employee.public"].browse(employee_id)
        # We will use the address of the employee or the partner of the company; the
        # goal is to check only the public holidays for a specific country.
        partner = employee.address_id or employee.company_id.partner_id
        list_by_dates = (
            self.env["calendar.public.holiday"]
            .get_holidays_list(
                start_dt=start_dt.date(),
                end_dt=end_dt.date(),
                partner_id=partner.id,
            )
            .mapped("date")
        )
        keys = (
            [r.id for r in resources]
            if resources
            else ([False] if False in intervals else [])
        )
        for key in keys:
            interval_resource = intervals.get(key)
            if not interval_resource:
                continue
            attendances = [
                attendance
                for attendance in interval_resource._items
                if attendance[0].date() not in list_by_dates
            ]
            intervals[key] = Intervals(attendances)
        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources_per_tz=None, domain=None
    ):
        res = super()._attendance_intervals_batch(
            start_dt=start_dt,
            end_dt=end_dt,
            resources_per_tz=resources_per_tz,
            domain=domain,
        )
        if self.env.context.get("exclude_public_holidays") and not domain:
            calendar = self
            resources = (
                self.env["resource.resource"].concat(*resources_per_tz.values())
                if resources_per_tz
                else self.env["resource.resource"]
            )
            if resources:
                employees = resources.employee_id
                if len(employees) == 1:
                    calendar = calendar.with_context(employee_id=employees.id)
            return calendar._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, res, resources
            )
        return res
