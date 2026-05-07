# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Get a real overview of leaves and work hours for an employee in a period."""
import dataclasses
import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta

import pytz

from odoo import models

_logger = logging.getLogger(__name__)


class _PeekableIterator:
    """Wraps a generator to provide hasNext()/next() peek semantics."""

    def __init__(self, iterable):
        self._iter = iter(iterable)
        self._exhausted = False
        self._peeked = None
        self._advance()

    def _advance(self):
        try:
            self._peeked = next(self._iter)
        except StopIteration:
            self._exhausted = True

    def hasNext(self):
        return not self._exhausted

    def next(self):
        value = self._peeked
        self._advance()
        return value


@dataclass
class WorkEntry:
    """A single work, leave, or holiday interval in the planning pipeline."""

    type: str
    datetime_from: datetime
    datetime_to: datetime
    holiday_name: str = None
    holiday_status_id: object = None

    @property
    def duration(self):
        return (self.datetime_to - self.datetime_from).total_seconds() / 3600


class TimeSlot:
    """A single work or leave slot within a day."""

    __slots__ = ("end_time", "start_time", "type")

    def __init__(self, start_time, end_time, slot_type):
        self.start_time = start_time
        self.end_time = end_time
        self.type = slot_type


class EmployeeDay:
    """Work and leave summary for a single employee on a single day."""

    __slots__ = ("date", "day_schedule", "hours_holiday", "hours_leave", "hours_work")

    def __init__(self, date):
        self.date = date
        self.hours_work = 0.0
        self.hours_leave = 0.0
        self.hours_holiday = 0.0
        self.day_schedule = []


class HrEmployee(models.Model):
    """Show advisor weekly planning."""

    _inherit = "hr.employee"

    def action_show_planning(self):
        self.ensure_one()
        wizard = self.env["hr.employee.planning"].create({"employee_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee.planning",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _get_work_hours_and_leaves_per_day(self, start_datetime, end_datetime):
        """For a single employee return a list of EmployeeDay objects, ordered on date.

        Covers all dates with scheduled work or approved leave between
        start_datetime and end_datetime (inclusive).

        Each EmployeeDay object has the following attributes:
            - date (datetime.date)
            - hours_work (float)
            - hours_leave (float)
            - day_schedule (list of TimeSlot)

        Each entry in day_schedule is a TimeSlot object with attributes:
            - start_time (datetime.time)
            - end_time (datetime.time)
            - type ("work" or "leave")

        Example:
            [
                EmployeeDay(
                    date=date(2026, 5, 21),
                    hours_work=8.0,
                    hours_leave=0.0,
                    day_schedule=[
                        TimeSlot(time(9, 0), time(17, 0), "work"),
                    ],
                ),
                EmployeeDay(
                    date=date(2026, 5, 22),
                    hours_work=4.0,
                    hours_leave=4.0,
                    day_schedule=[
                        TimeSlot(time(9, 0), time(11, 0), "work"),
                        TimeSlot(time(11, 0), time(15, 0), "leave"),
                        TimeSlot(time(15, 0), time(17, 0), "work"),
                    ],
                ),
            ]
        """
        self.ensure_one()
        work_hours_and_leaves_per_day = []
        work_and_leaves = self._get_work_hours_and_leaves(start_datetime, end_datetime)
        current_day = None
        for entry in work_and_leaves:
            entry_date = entry.datetime_from.date()
            if current_day is None or current_day.date != entry_date:
                current_day = EmployeeDay(entry_date)
                work_hours_and_leaves_per_day.append(current_day)
            if entry.type == "work":
                current_day.hours_work += entry.duration
            elif entry.type == "holiday":
                current_day.hours_holiday += entry.duration
            else:
                current_day.hours_leave += entry.duration
            current_day.day_schedule.append(
                TimeSlot(
                    entry.datetime_from.time(),
                    entry.datetime_to.time(),
                    entry.type,
                )
            )
        return work_hours_and_leaves_per_day

    def _get_work_hours_and_leaves(self, start_datetime, end_datetime):
        """Return a merged, chronological list of WorkEntry objects.

        Calls _get_work_per_day and _get_leaves_per_day (which already merges
        approved leaves and public holidays, with holidays taking precedence),
        then advances both generators in parallel — similar to a merge-sort step
        — comparing start datetimes to decide which entry to emit next.

        Overlapping intervals are split so that work and leave/holiday blocks
        never overlap in the output.  The six overlap cases handled are:

        1. Leave ends before work starts: discard the leave entry and advance
           the leave iterator (the leave was already emitted as a per-slot copy
           or belongs to a non-working day).
        2. Work ends before leave starts: emit the work slot as-is and advance
           the work iterator.
        3. Leave fully covers work (leave_from <= work_from AND
           leave_to >= work_to): emit a per-slot copy of the leave clipped to
           the work slot's hours so that _get_work_hours_and_leaves_per_day
           places it on the correct date.  Advance work only; the same leave
           may cover subsequent work slots.
        4. Leave is entirely within work (leave_from >= work_from AND
           leave_to <= work_to): emit work before the leave (if any), the
           leave, and work after the leave (if any).  Advance both iterators.
        5. Leave starts before work and ends during it: emit a clipped copy of
           the leave starting at work_from, then the remaining work from
           leave_to onward.  Advance both iterators.
        6. Leave starts during work and extends beyond it: emit work up to
           leave_from, then emit the leave clipped to work_to.  Trim the
           leave to start at work_to and advance work; the trimmed leave will
           be matched against subsequent work slots (or discarded by Case 1 if
           it ends within the same day's non-working hours).

        start_datetime and end_datetime must be naive UTC datetimes.
        Each entry in the returned list is a WorkEntry with attributes type
        ("work", "leave", or "holiday"), datetime_from, datetime_to, and
        optional holiday_name / holiday_status_id.  Duration is available via
        the WorkEntry.duration property.
        """
        self.ensure_one()
        self._check_resource_calendar()
        work_and_leaves = []
        work_days = _PeekableIterator(
            self._get_work_per_day(start_datetime, end_datetime)
        )
        leave_days = _PeekableIterator(
            self._get_leaves_per_day(start_datetime, end_datetime)
        )
        work = work_days.next() if work_days.hasNext() else None
        leave = leave_days.next() if leave_days.hasNext() else None
        while work is not None or leave is not None:
            if work is None:
                # All work slots processed; remaining leaves don't affect any slot.
                break
            if leave is None:
                # No more leaves; flush remaining work.
                work_and_leaves.append(work)
                work = work_days.next() if work_days.hasNext() else None
            elif leave.datetime_to <= work.datetime_from:
                # Leave ended before this work slot; discard it.
                leave = leave_days.next() if leave_days.hasNext() else None
            elif leave.datetime_from >= work.datetime_to:
                # Leave starts after this work slot ends; emit work, keep leave.
                work_and_leaves.append(work)
                work = work_days.next() if work_days.hasNext() else None
            elif (
                leave.datetime_from <= work.datetime_from
                and leave.datetime_to >= work.datetime_to
            ):
                # Leave fully covers this work slot.
                # Emit a per-slot copy clipped to work hours so that
                # _get_work_hours_and_leaves_per_day places it on the right date.
                work_and_leaves.append(
                    dataclasses.replace(
                        leave,
                        datetime_from=work.datetime_from,
                        datetime_to=work.datetime_to,
                    )
                )
                work = work_days.next() if work_days.hasNext() else None
                # Do not advance leave; it may cover subsequent work slots.
            elif (
                leave.datetime_from >= work.datetime_from
                and leave.datetime_to <= work.datetime_to
            ):
                # Leave is entirely within this work slot.
                if leave.datetime_from > work.datetime_from:
                    work_and_leaves.append(
                        dataclasses.replace(work, datetime_to=leave.datetime_from)
                    )
                work_and_leaves.append(leave)
                if leave.datetime_to < work.datetime_to:
                    work_and_leaves.append(
                        dataclasses.replace(work, datetime_from=leave.datetime_to)
                    )
                # TODO: handle work interrupted multiple times by leave.
                work = work_days.next() if work_days.hasNext() else None
                leave = leave_days.next() if leave_days.hasNext() else None
            elif leave.datetime_from < work.datetime_from:
                # Leave started before this work slot and ends during it.
                work_and_leaves.append(
                    dataclasses.replace(leave, datetime_from=work.datetime_from)
                )
                if leave.datetime_to < work.datetime_to:
                    work_and_leaves.append(
                        dataclasses.replace(work, datetime_from=leave.datetime_to)
                    )
                work = work_days.next() if work_days.hasNext() else None
                leave = leave_days.next() if leave_days.hasNext() else None
            else:
                # Leave starts during this work slot and extends beyond it.
                # Emit work up to where the leave starts.
                work_and_leaves.append(
                    dataclasses.replace(work, datetime_to=leave.datetime_from)
                )
                # Emit the leave portion that falls within this work slot.
                work_and_leaves.append(
                    dataclasses.replace(leave, datetime_to=work.datetime_to)
                )
                # Trim leave to start after this work slot; it may still cover
                # subsequent work slots (e.g. multi-day leave), or will be
                # discarded by Case 1 if it ends in non-working hours.
                leave = dataclasses.replace(leave, datetime_from=work.datetime_to)
                work = work_days.next() if work_days.hasNext() else None
        return work_and_leaves

    def _check_resource_calendar(self):
        """Warn if the employee's user timezone differs from the work calendar timezone."""
        self.ensure_one()
        if (
            self.user_id
            and self.user_id.partner_id.tz
            and self.user_id.partner_id.tz != self.resource_calendar_id.tz
        ):
            _logger.warn(
                "Employee %(employee)s timezone %(employee_tz)s not the same"
                " as calendar timezone %(calendar_tz)s",
                {
                    "employee": self.name,
                    "employee_tz": self.user_id.partner_id.tz,
                    "calendar_tz": self.resource_calendar_id.tz,
                },
            )

    def _get_work_per_day(self, start_datetime, end_datetime):
        """Yield working times one by one from start to end."""
        self.ensure_one()
        datetime_from = self._get_employee_datetime(start_datetime)
        date_from = datetime_from.date()
        datetime_to = self._get_employee_datetime(end_datetime)
        date_to = datetime_to.date()
        Attendance = self.env["resource.calendar.attendance"]
        attendances = Attendance.search(
            [
                ("calendar_id", "=", self.resource_calendar_id.id),
                ("display_type", "=", False),
                "|",
                ("date_from", "=", False),
                ("date_from", ">=", date_from),
                "|",
                ("date_to", "=", False),
                ("date_to", ">=", date_to),
            ],
            order="week_type, dayofweek, hour_from",
        )
        attendance_dict = {}
        for attendance in attendances:
            attendance_key = (attendance.week_type, attendance.dayofweek)
            if attendance_key not in attendance_dict:
                attendance_dict[attendance_key] = []
            attendance_dict[attendance_key].append(attendance)
        current_date = date_from
        while current_date <= date_to:
            attendance_list = attendance_dict.get(
                self._get_date_attendance_key(current_date), []
            )
            for attendance in attendance_list:
                yield self._fill_work_hours(current_date, attendance)
            current_date += timedelta(days=1)

    def _get_employee_datetime(self, utc_datetime):
        """Convert a naive datetime, known to be utc, to a localized datetime."""
        self.ensure_one()
        local_timezone = pytz.timezone(self.tz)
        return utc_datetime.replace(tzinfo=pytz.utc).astimezone(local_timezone)

    def _get_date_attendance_key(self, date):
        """Attendance key depends on odd/even week and day of week."""
        # week_type 0 is even week, 1 is odd week. Only for two week calendars.
        dayofweek = str(date.weekday())
        calendar = self.resource_calendar_id
        # Odoo has its own definition of what are odd or even weeks, that
        # can differ from what you would guess from the weeknumber!!
        week_type = (
            str(self.env["resource.calendar.attendance"].get_week_type(date))
            if calendar.two_weeks_calendar
            else False
        )
        return (week_type, dayofweek)

    def _fill_work_hours(self, date, attendance):
        hours_from, minutes_from = self._time_to_hours_minutes(attendance.hour_from)
        hours_to, minutes_to = self._time_to_hours_minutes(attendance.hour_to)
        datetime_from = datetime.combine(date, time(hours_from, minutes_from))
        datetime_to = datetime.combine(date, time(hours_to, minutes_to))
        local_timezone = pytz.timezone(self.tz)
        return WorkEntry(
            type="work",
            datetime_from=local_timezone.localize(datetime_from),
            datetime_to=local_timezone.localize(datetime_to),
        )

    def _time_to_hours_minutes(self, float_value):
        hours = int(float_value)
        minutes = int((float_value - hours) * 60)
        return hours, minutes

    def _get_leaves_per_day(self, start_datetime, end_datetime):
        """Yield approved leaves and public holidays from start to end.

        Public holidays take precedence: when a leave overlaps with a public
        holiday, the holiday is returned for that portion and the leave is
        trimmed around it.  Entries are yielded in ascending datetime_from
        order.

        For full-day leaves (is_full_day=True), one midnight-to-midnight entry
        is generated per calendar day so the merge algorithm clips each day to
        the *current* work schedule.  This keeps results correct even when the
        work schedule is modified after the leave was registered.  Partial
        leaves use the exact stored start/end times.
        """
        self.ensure_one()
        local_timezone = pytz.timezone(self.tz)
        date_from = self._get_employee_datetime(start_datetime).date()
        date_to = self._get_employee_datetime(end_datetime).date()

        # Build holiday entries (full calendar day: 00:00 → 00:00 next day).
        holiday_entries = []
        holiday_dates = set()
        for line in self._get_public_holiday_lines(date_from, date_to):
            dt_from = local_timezone.localize(datetime.combine(line.date, time.min))
            dt_to = local_timezone.localize(
                datetime.combine(line.date + timedelta(days=1), time.min)
            )
            holiday_entries.append(
                WorkEntry(
                    type="holiday",
                    datetime_from=dt_from,
                    datetime_to=dt_to,
                    holiday_name=line.name,
                )
            )
            holiday_dates.add(line.date)

        # Build leave entries split around any overlapping holiday days.
        leave_entries = []
        leaves = self.env["hr.leave"].search(
            [
                ("employee_id", "=", self.id),
                ("state", "=", "validate"),
                ("date_from", "<", end_datetime),
                ("date_to", ">", start_datetime),
            ],
            order="date_from",
        )
        for leave in leaves:
            if not leave.request_unit_half and not leave.request_unit_hours:
                # Generate one midnight-to-midnight entry per calendar day so
                # the merge algorithm clips it to the current work schedule,
                # regardless of schedule changes since registration.
                dt_from_local = leave.date_from.replace(tzinfo=pytz.utc).astimezone(
                    local_timezone
                )
                dt_to_local = leave.date_to.replace(tzinfo=pytz.utc).astimezone(
                    local_timezone
                )
                # A leave ending exactly at midnight belongs to the previous
                # day (e.g. date_to Tue 00:00 means the last active day is Mon).
                end_date = (
                    dt_to_local.date() - timedelta(days=1)
                    if dt_to_local.time() == time.min
                    else dt_to_local.date()
                )
                current_date = dt_from_local.date()
                while current_date <= end_date:
                    day_from = local_timezone.localize(
                        datetime.combine(current_date, time.min)
                    )
                    day_to = local_timezone.localize(
                        datetime.combine(current_date + timedelta(days=1), time.min)
                    )
                    entry = WorkEntry(
                        type="leave",
                        datetime_from=day_from,
                        datetime_to=day_to,
                        holiday_status_id=leave.holiday_status_id,
                    )
                    leave_entries.extend(
                        self._split_entry_around_holidays(
                            entry, holiday_dates, local_timezone
                        )
                    )
                    current_date += timedelta(days=1)
            else:
                # Partial leave: Odoo stores date_from/date_to as naive UTC;
                # convert to the employee's timezone and use as-is.
                dt_from = leave.date_from.replace(tzinfo=pytz.utc).astimezone(
                    local_timezone
                )
                dt_to = leave.date_to.replace(tzinfo=pytz.utc).astimezone(
                    local_timezone
                )
                entry = WorkEntry(
                    type="leave",
                    datetime_from=dt_from,
                    datetime_to=dt_to,
                    holiday_status_id=leave.holiday_status_id,
                )
                leave_entries.extend(
                    self._split_entry_around_holidays(
                        entry, holiday_dates, local_timezone
                    )
                )

        yield from sorted(
            holiday_entries + leave_entries,
            key=lambda e: e.datetime_from,
        )

    def _get_public_holiday_lines(self, date_from, date_to):
        """Return public holiday lines applicable to this employee in the date range.

        Iterates over every calendar year that overlaps [date_from, date_to].
        For each year, calls ``hr.holidays.public.get_holidays_list(year,
        employee=self)``, which already restricts results to holidays that apply
        to the employee's country and state.  The per-year results are then
        filtered a second time to keep only lines whose date falls within the
        requested range (necessary because ``get_holidays_list`` returns all
        holidays for the full year).  Lines from all years are combined and
        returned sorted ascending by date.
        """
        HrHolidaysPublic = self.env["hr.holidays.public"]
        lines = self.env["hr.holidays.public.line"].browse()
        for year in range(date_from.year, date_to.year + 1):
            year_lines = HrHolidaysPublic.get_holidays_list(year, employee_id=self.id)
            lines |= year_lines.filtered(
                lambda l, f=date_from, t=date_to: f <= l.date <= t
            )
        return lines.sorted("date")

    def _split_entry_around_holidays(self, entry, holiday_dates, local_timezone):
        """Return copies of entry with any holiday-day portions removed.

        Finds all dates in *holiday_dates* that fall within the entry's date
        range, then walks through them in chronological order.  For each
        holiday date:

        - If the current tail of the entry starts before the holiday's
          midnight, a copy of the entry is emitted covering
          [current_from, holiday midnight).
        - The current position is then advanced to midnight of the day *after*
          the holiday, effectively discarding that calendar day from the entry.

        After all holidays have been processed, any remaining portion
        [last_holiday_end, entry end) is emitted as a final copy.

        If no holiday overlaps with the entry, the original entry is returned
        unchanged inside a single-element list.  If the entry falls entirely
        within holiday days, all portions are discarded and an empty list is
        returned.
        """
        dt_from = entry.datetime_from
        dt_to = entry.datetime_to
        overlapping = sorted(
            h for h in holiday_dates if dt_from.date() <= h <= dt_to.date()
        )
        if not overlapping:
            return [entry]
        result = []
        current_from = dt_from
        for holiday_date in overlapping:
            holiday_start = local_timezone.localize(
                datetime.combine(holiday_date, time.min)
            )
            if current_from < holiday_start:
                result.append(
                    dataclasses.replace(
                        entry,
                        datetime_from=current_from,
                        datetime_to=holiday_start,
                    )
                )
            current_from = local_timezone.localize(
                datetime.combine(holiday_date + timedelta(days=1), time.min)
            )
        if current_from < dt_to:
            result.append(
                dataclasses.replace(
                    entry, datetime_from=current_from, datetime_to=dt_to
                )
            )
        return result
