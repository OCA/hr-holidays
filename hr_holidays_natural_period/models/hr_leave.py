# Copyright 2020-2024 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Carlos Lopez
# Copyright 2025 Grupo Isonor - Alexandre D. Díaz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from datetime import time as dt_time
from datetime import timezone as dt_timezone

from odoo import fields, models
from odoo.tools.date_utils import end_of, start_of
from odoo.tools.float_utils import float_round

from odoo.addons.resource.models.utils import HOURS_PER_DAY


class HrLeave(models.Model):
    """Extensions to handle natural day leave durations."""

    _inherit = "hr.leave"

    def _is_natural_day_leave_type(self) -> bool:
        """
        Check if this leave uses natural day calculation.

        Natural day calculation counts all calendar days (including weekends)
        rather than just working days.

        Returns:
            bool: True if this is a natural_day leave type
        """
        mod_holidays_status_ids = self.env.context.get("mod_holidays_status_ids", [])
        is_mod_leave_type = self.holiday_status_id.id in mod_holidays_status_ids
        return is_mod_leave_type or (
            self.holiday_status_id.request_unit == "natural_day"
        )

    def _get_public_holiday_dates(
        self, start_date, end_date, resource_calendar=None
    ) -> set:
        """Return set of public holiday dates from Odoo core and hr_holidays_public."""
        self.ensure_one()
        dates: set = set()
        resource_calendar = resource_calendar or self.resource_calendar_id

        # Core: resource.calendar.leaves (global to the calendar)
        if resource_calendar:
            day_start = datetime.combine(start_date, dt_time.min)
            day_end = datetime.combine(end_date, dt_time.max)
            core_leaves = self.env["resource.calendar.leaves"].search(
                [
                    ("calendar_id", "=", resource_calendar.id),
                    ("resource_id", "=", False),
                    ("date_from", "<=", day_end),
                    ("date_to", ">=", day_start),
                ]
            )
            # Convert to the resource calendar timezone before extracting dates
            cal_tz_name = (
                (resource_calendar and resource_calendar.tz)
                or (self.employee_id and self.employee_id.tz)
                or self.env.user.tz
                or "UTC"
            )
            env_tz = self.with_context(tz=cal_tz_name)
            for leave in core_leaves:
                # Full UTC-day heuristic: 00:00:00 to 23:59:59 on same UTC date
                is_full_utc_day = (
                    leave.date_from.time() == dt_time.min
                    and leave.date_to.time().hour == 23
                    and leave.date_to.time().minute == 59
                    and leave.date_from.date() == leave.date_to.date()
                )
                local_from = fields.Datetime.context_timestamp(env_tz, leave.date_from)
                local_to = fields.Datetime.context_timestamp(env_tz, leave.date_to)
                if is_full_utc_day:
                    # Treat as a single local holiday date (intended one-day PH)
                    dates.add(local_from.date())
                    continue
                ls, le = local_from.date(), local_to.date()
                dates.update(
                    {ls + timedelta(days=o) for o in range((le - ls).days + 1)}
                )

        # OCA: hr_holidays_public (if installed)
        if "hr.holidays.public" in self.env:
            lines = self.env["hr.holidays.public"].get_holidays_list(
                start_dt=start_date,
                end_dt=end_date,
                employee_id=self.employee_id.id if self.employee_id else None,
            )
            dates.update({line.date for line in lines})
        return dates

    def _calculate_natural_day_duration(
        self, resource_calendar, _domain: list
    ) -> tuple[float, float]:
        """
        Calculate duration for natural_day leave types using date arithmetic and,
        optionally, hr_holidays_public to exclude public holidays.
        """
        # Resolve start/end as dates from date_from/date_to
        # (ignore request_date_* for natural days)
        cal_tz_name = (
            (resource_calendar and resource_calendar.tz)
            or (self.employee_id and self.employee_id.tz)
            or self.env.user.tz
            or "UTC"
        )
        env_tz = self.with_context(tz=cal_tz_name)
        local_from = fields.Datetime.context_timestamp(env_tz, self.date_from)
        local_to = fields.Datetime.context_timestamp(env_tz, self.date_to)
        if self.request_date_from and self.request_date_to:
            # Use explicit request dates if provided to avoid TZ boundary off-by-one
            start_date = self.request_date_from
            end_date = self.request_date_to
        else:
            start_date = local_from.date()
            end_date = local_to.date()

        if start_date > end_date:
            return 0.0, 0.0

        # Inclusive date set
        total_dates = {
            start_date + timedelta(days=offset)
            for offset in range((end_date - start_date).days + 1)
        }

        # Optionally exclude public holidays (context or leave type flag)
        exclude_ctx = self.env.context.get("exclude_public_holidays", False)
        exclude_type = getattr(self.holiday_status_id, "exclude_public_holidays", False)
        if (exclude_ctx or exclude_type) and self.employee_id:
            ph_dates = self._get_public_holiday_dates(
                start_date, end_date, resource_calendar=resource_calendar
            )
            total_dates.difference_update(ph_dates)

        # Number of days is authoritative for natural_day.
        # Compatibility: set hours equal to days because some allocation paths
        # read number_of_hours as a “days-like” magnitude without division.
        days = float(len(total_dates))
        hours = days
        return days, hours

    def _get_duration(
        self, check_leave_type: bool = True, resource_calendar=None
    ) -> tuple[float, float]:
        """
        Calculate leave duration in days and hours.

        This method reimplements the core logic for natural_day leave types
        without field modifications to avoid cascading ORM recomputations.

        Args:
            check_leave_type: Whether to check leave type for calculations
            resource_calendar: Resource calendar to use (defaults to employee's)

        Returns:
            Tuple[float, float]: (days, hours) duration
        """
        self.ensure_one()
        resource_calendar = resource_calendar or self.resource_calendar_id

        if not self.date_from or not self.date_to or not resource_calendar:
            return (0.0, 0.0)

        is_natural_day = self._is_natural_day_leave_type()

        if is_natural_day and check_leave_type:
            # Natural day branch (keeps current behavior)
            domain = [
                ("time_type", "=", "leave"),
                (
                    "company_id",
                    "in",
                    self.env.companies.ids
                    + self.env.context.get("allowed_company_ids", []),
                ),
                "|",
                ("holiday_id", "=", False),
                ("holiday_id", "!=", self.id),
            ]
            if self.employee_id:
                days, hours = self._calculate_natural_day_duration(
                    resource_calendar, domain
                )
            else:
                # Employee-less natural day fallback
                days, hours = self._calculate_employee_less_duration(resource_calendar)
        else:
            # Non-natural leaves: delegate to super to keep hr_holidays_public behavior
            return super()._get_duration(
                check_leave_type=check_leave_type, resource_calendar=resource_calendar
            )

        # Apply ceiling only for day-based leave types (natural_day or day)
        if is_natural_day and check_leave_type:
            days = float_round(days, precision_rounding=1, rounding_method="UP")

        return (days, hours)

    def _calculate_employee_less_duration(
        self, resource_calendar
    ) -> tuple[float, float]:
        """
        Calculate duration for leaves without assigned employee.

        Uses resource calendar directly to compute work hours for the period,
        then estimates days based on typical daily hours.

        Args:
            resource_calendar: Resource calendar for calculations

        Returns:
            Tuple[float, float]: (days, hours) estimated duration
        """
        date_from, date_to = self.date_from, self.date_to
        cal_tz_name = resource_calendar.tz or self.env.user.tz or "UTC"
        env_tz = self.with_context(tz=cal_tz_name)
        local_from = fields.Datetime.context_timestamp(env_tz, date_from)
        local_day_start = start_of(local_from, "day")
        local_day_end = end_of(local_from, "day")
        day_start = local_day_start.astimezone(dt_timezone.utc).replace(tzinfo=None)
        day_end = local_day_end.astimezone(dt_timezone.utc).replace(tzinfo=None)

        today_hours = resource_calendar.get_work_hours_count(day_start, day_end, False)
        total_hours = resource_calendar.get_work_hours_count(date_from, date_to)
        divisor = today_hours if today_hours else HOURS_PER_DAY
        estimated_days = float_round(total_hours / divisor, precision_rounding=0.001)

        return estimated_days, total_hours
