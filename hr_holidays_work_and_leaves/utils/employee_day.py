# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from dataclasses import dataclass
from datetime import datetime, time, timedelta


def _time_to_float(t):
    """Return hours since midnight; time(0, 0) used as end-of-day sentinel = 24.0."""
    return 24.0 if t == time(0, 0) else t.hour + t.minute / 60.0


@dataclass
class WorkEntry:
    """A single work, leave, or holiday interval in the planning pipeline."""

    type: str
    datetime_from: datetime
    datetime_to: datetime
    holiday_name: str = None
    holiday_status_id: object = None
    name: str = None

    @property
    def duration(self):
        return (self.datetime_to - self.datetime_from).total_seconds() / 3600


class TimeSlot:
    """A single work or leave slot within a day."""

    __slots__ = ("end_time", "hours_overlap_work", "name", "start_time", "type")

    def __init__(self, start_time, end_time, slot_type, name=None):
        self.start_time = start_time
        self.end_time = end_time
        self.type = slot_type
        self.hours_overlap_work = 0.0
        self.name = name


class EmployeeDay:
    """Work and leave summary for a single employee on a single day."""

    __slots__ = (
        "date",
        "day_schedule",
        "hours_appointment",
        "hours_holiday",
        "hours_leave",
        "hours_leave_requested",
        "hours_work",
    )

    def __init__(self, date):
        self.date = date
        self.hours_work = 0.0
        self.hours_leave = 0.0
        self.hours_holiday = 0.0
        self.hours_leave_requested = 0.0
        self.hours_appointment = 0.0
        self.day_schedule = []

    def insert_slot(self, slot):
        """Insert slot into day_schedule, maintaining order by start_time."""
        for idx, ts in enumerate(self.day_schedule):
            if ts.start_time > slot.start_time:
                self.day_schedule.insert(idx, slot)
                return
        self.day_schedule.append(slot)

    def compute_slot_work_overlap(self, slot_from_time, slot_to_time):
        """Return total hours that [slot_from_time, slot_to_time) overlaps work slots."""
        a = 0.0 if slot_from_time == time(0, 0) else _time_to_float(slot_from_time)
        b = _time_to_float(slot_to_time)
        total = 0.0
        for ts in self.day_schedule:
            if ts.type != "work":
                continue
            c = ts.start_time.hour + ts.start_time.minute / 60.0
            d = _time_to_float(ts.end_time)
            total += max(0.0, min(b, d) - max(a, c))
        return total


class EmployeeDaySchedule:
    """Ordered collection of EmployeeDay objects, indexed by date for fast lookup."""

    def __init__(self, days):
        self._days = days
        self._days_by_date = {day.date: day for day in days}

    def __iter__(self):
        return iter(self._days)

    def add_to_days(self, date_from, date_to, slot_type, name):
        """Insert a leave or appointment slot into every day it overlaps with work."""
        end_date = (
            date_to.date() - timedelta(days=1)
            if date_to.time() == time(0, 0)
            else date_to.date()
        )
        current_date = date_from.date()
        while current_date <= end_date:
            day_entry = self._days_by_date.get(current_date)
            if day_entry is not None:
                slot_from_time = (
                    date_from.time() if current_date == date_from.date() else time(0, 0)
                )
                slot_to_time = (
                    date_to.time() if current_date == date_to.date() else time(0, 0)
                )
                overlap = day_entry.compute_slot_work_overlap(
                    slot_from_time, slot_to_time
                )
                if overlap > 0.0:
                    slot = TimeSlot(slot_from_time, slot_to_time, slot_type, name=name)
                    slot.hours_overlap_work = overlap
                    day_entry.insert_slot(slot)
                    if slot_type == "leave_requested":
                        day_entry.hours_leave_requested += overlap
                    elif slot_type == "appointment":
                        day_entry.hours_appointment += overlap
            current_date += timedelta(days=1)
