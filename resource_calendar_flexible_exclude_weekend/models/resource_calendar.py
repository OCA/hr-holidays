# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from collections import defaultdict
from datetime import timedelta

from dateutil.rrule import DAILY, rrule
from pytz import timezone

from odoo import fields, models
from odoo.fields import Domain
from odoo.tools.intervals import Intervals

_logger = logging.getLogger(__name__)


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    exclude_weekends = fields.Boolean()

    # Override to return weekends as special days if exclude_weekends is set
    def _attendance_intervals_batch(  # noqa: C901
        self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False
    ):
        """
        Override to adjust start_dt if it falls on a weekend.
        - Convert start_dt to the relevant timezone
        - If Saturday or Sunday → move to next Monday
        - Then call super() with the adjusted start_dt
        """
        # Ensure timezone awareness
        assert start_dt.tzinfo and end_dt.tzinfo, "Datetimes must be timezone-aware"
        self.ensure_one()

        # shortcut: the method can be called with and end_dt before start_dt,
        # in this case the expected value is a dictionary with empty intervals.
        if end_dt < start_dt:
            return super()._attendance_intervals_batch(
                start_dt, end_dt, resources, domain, tz, lunch
            )
        if not resources:
            resources = self.env["resource.resource"]
            resources_list = [resources]
        else:
            resources_list = list(resources) + [self.env["resource.resource"]]

        resources_with_flex_no_weekend = []
        other_resources = []
        for resource in resources_list:
            if (
                resource
                and resource.calendar_id.flexible_hours
                and resource.calendar_id.exclude_weekends
            ) or (self.flexible_hours and self.exclude_weekends):
                resources_with_flex_no_weekend.append(resource)
            else:
                other_resources.append(resource)
        if other_resources:
            res_others = super()._attendance_intervals_batch(
                start_dt,
                end_dt,
                sum(other_resources, self.env["resource.resource"]),
                domain,
                tz,
                lunch,
            )
        else:
            # containing resources (empty or not)
            res_others = {}
        if resources_with_flex_no_weekend:
            skipping_res = defaultdict(dict)
            resources_per_tz = defaultdict(list)
            for resource in resources_with_flex_no_weekend:
                resources_per_tz[tz or timezone((resource or self).tz)].append(resource)
            for tz, tz_resources in resources_per_tz.items():
                skipping_start_dt = start_dt.astimezone(tz)
                # 0=Monday, 6=Sunday
                weekday = skipping_start_dt.weekday()
                if weekday in (5, 6):  # Saturday or Sunday
                    # Move to next Monday, midnight in the considered TZ
                    days_to_monday = 7 - weekday
                    skipping_start_dt += timedelta(days=days_to_monday, hours=1)
                    # reconvert to get Daylight saving time applied if needed
                    skipping_start_dt = skipping_start_dt.astimezone(tz)
                    skipping_start_dt -= timedelta(
                        hours=skipping_start_dt.hour,
                        minutes=skipping_start_dt.minute,
                        seconds=skipping_start_dt.second,
                    )
                    # check if we moved past the end date, in which case we want to move
                    # it to ensure we enter the while loop below
                    if end_dt < skipping_start_dt:
                        end_dt = skipping_start_dt

                # for resources which should skip weekend we have to iterate by week
                # I thought that maybe we can be smarter and only do 1 or 2 calls:
                # 1 call if the first day is a monday, and a second if we need to
                # check the following week, but this does not work when there are
                # holidays in the period
                while skipping_start_dt <= end_dt:
                    # find the end of the current week or the end of the period
                    skipping_end_dt = (
                        skipping_start_dt
                        + timedelta(days=7 - skipping_start_dt.weekday(), hours=1)
                    ).astimezone(tz)
                    skipping_end_dt -= timedelta(
                        hours=skipping_end_dt.hour,
                        minutes=skipping_end_dt.minute,
                        seconds=skipping_end_dt.second,
                    )
                    skipping_end_dt = min(skipping_end_dt, end_dt)
                    res_skip = super()._attendance_intervals_batch(
                        skipping_start_dt,
                        skipping_end_dt,
                        sum(tz_resources, self.env["resource.resource"]),
                        domain,
                        tz,
                        lunch,
                    )
                    for resource_id, work_intervals in res_skip.items():
                        new_intervals = skipping_res[resource_id]
                        for start, end, attendance in work_intervals:
                            if start.weekday() not in (5, 6):
                                new_intervals[(start, end)] = (start, end, attendance)
                    if skipping_end_dt.date() >= end_dt.date():
                        # skipping_end_dt is always local-midnight-aligned,
                        # while end_dt is a UTC day boundary: for any
                        # non-UTC, positive offset it lands a few hours past
                        # local midnight once interpreted in this timezone,
                        # so it can never equal skipping_end_dt exactly
                        # (they are genuinely different instants, not just
                        # different representations of the same one).
                        # Comparing on the calendar date instead of exact
                        # datetime equality avoids running one bogus extra
                        # iteration for that timezone-conversion artifact,
                        # which would otherwise open a new week with a
                        # fresh weekly-hours budget for a few leftover
                        # hours that don't represent a real elapsed day.
                        break
                    else:
                        # go to next monday
                        skipping_start_dt = skipping_end_dt
            # merge both result set
            for resource_id, intervals in skipping_res.items():
                res_others[resource_id] = Intervals(
                    intervals.values(), keep_distinct=True
                )
        return res_others

    def _get_unusual_days(self, start_dt, end_dt, company_id=False):
        if self.flexible_hours and self.exclude_weekends:
            # when we exclude weekend, use the same implementation as
            # for non flexible hours
            utc = timezone("UTC")
            if not start_dt.tzinfo:
                start_dt = start_dt.replace(tzinfo=utc)
            if not end_dt.tzinfo:
                end_dt = end_dt.replace(tzinfo=utc)
            domain = Domain(True)
            if company_id:
                domain = Domain("company_id", "in", (company_id.id, False))
            works = {
                d[0].date()
                for d in self._work_intervals_batch(start_dt, end_dt, domain=domain)[
                    False
                ]
            }
            return {
                fields.Date.to_string(day.date()): (day.date() not in works)
                for day in rrule(DAILY, start_dt, until=end_dt)
            }
        else:
            return super()._get_unusual_days(start_dt, end_dt, company_id)
