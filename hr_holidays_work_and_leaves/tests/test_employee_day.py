# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import unittest
from datetime import date, datetime, time

from ..utils.employee_day import EmployeeDay, EmployeeDaySchedule, TimeSlot


def _work_day(d, start_hour=9, end_hour=17):
    """Return an EmployeeDay with a single work slot."""
    day = EmployeeDay(d)
    day.day_schedule.append(TimeSlot(time(start_hour, 0), time(end_hour, 0), "work"))
    return day


class TestEmployeeDayInsertSlot(unittest.TestCase):
    def test_insert_into_empty_schedule(self):
        day = EmployeeDay(date(2026, 6, 1))
        slot = TimeSlot(time(10, 0), time(11, 0), "leave")
        day.insert_slot(slot)
        self.assertEqual(day.day_schedule, [slot])

    def test_insert_before_existing(self):
        day = EmployeeDay(date(2026, 6, 1))
        late = TimeSlot(time(14, 0), time(15, 0), "leave")
        early = TimeSlot(time(10, 0), time(11, 0), "leave")
        day.insert_slot(late)
        day.insert_slot(early)
        self.assertEqual(day.day_schedule, [early, late])

    def test_insert_after_existing(self):
        day = EmployeeDay(date(2026, 6, 1))
        early = TimeSlot(time(10, 0), time(11, 0), "leave")
        late = TimeSlot(time(14, 0), time(15, 0), "leave")
        day.insert_slot(early)
        day.insert_slot(late)
        self.assertEqual(day.day_schedule, [early, late])

    def test_insert_in_middle(self):
        day = EmployeeDay(date(2026, 6, 1))
        first = TimeSlot(time(9, 0), time(10, 0), "work")
        third = TimeSlot(time(14, 0), time(17, 0), "work")
        middle = TimeSlot(time(11, 0), time(13, 0), "leave")
        day.insert_slot(first)
        day.insert_slot(third)
        day.insert_slot(middle)
        self.assertEqual(day.day_schedule, [first, middle, third])


class TestEmployeeDayComputeSlotWorkOverlap(unittest.TestCase):
    def test_no_work_slots_returns_zero(self):
        day = EmployeeDay(date(2026, 6, 1))
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(10, 0), time(11, 0)), 0.0
        )

    def test_non_work_slots_are_ignored(self):
        day = EmployeeDay(date(2026, 6, 1))
        day.day_schedule.append(TimeSlot(time(9, 0), time(17, 0), "leave"))
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(10, 0), time(11, 0)), 0.0
        )

    def test_slot_fully_within_work(self):
        day = _work_day(date(2026, 6, 1))
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(10, 0), time(12, 0)), 2.0
        )

    def test_slot_fully_outside_work(self):
        day = _work_day(date(2026, 6, 1))
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(18, 0), time(19, 0)), 0.0
        )

    def test_slot_overlaps_work_start(self):
        day = _work_day(date(2026, 6, 1))
        # 07:00–10:00, work starts at 09:00 → 1 hour overlap.
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(7, 0), time(10, 0)), 1.0
        )

    def test_slot_overlaps_work_end(self):
        day = _work_day(date(2026, 6, 1))
        # 16:00–19:00, work ends at 17:00 → 1 hour overlap.
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(16, 0), time(19, 0)), 1.0
        )

    def test_midnight_to_midnight_covers_full_work_day(self):
        """time(0, 0) as both from and to is treated as 00:00–24:00."""
        day = _work_day(date(2026, 6, 1))
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(0, 0), time(0, 0)), 8.0
        )

    def test_multiple_work_slots_accumulates(self):
        """Overlap is summed across all work slots."""
        day = EmployeeDay(date(2026, 6, 1))
        day.day_schedule.append(TimeSlot(time(9, 0), time(12, 0), "work"))
        day.day_schedule.append(TimeSlot(time(13, 0), time(17, 0), "work"))
        # 10:00–16:00: overlaps 10–12 (2h) and 13–16 (3h) = 5h.
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(10, 0), time(16, 0)), 5.0
        )

    def test_slot_spanning_lunch_gap_excludes_gap(self):
        """A slot spanning a gap between two work blocks excludes the gap."""
        day = EmployeeDay(date(2026, 6, 1))
        day.day_schedule.append(TimeSlot(time(9, 0), time(12, 0), "work"))
        day.day_schedule.append(TimeSlot(time(13, 0), time(17, 0), "work"))
        # 11:00–14:00: overlaps 11–12 (1h) and 13–14 (1h) = 2h, gap excluded.
        self.assertAlmostEqual(
            day.compute_slot_work_overlap(time(11, 0), time(14, 0)), 2.0
        )


class TestEmployeeDaySchedule(unittest.TestCase):
    def test_iter_empty(self):
        self.assertEqual(list(EmployeeDaySchedule([])), [])

    def test_iter_preserves_order(self):
        days = [
            _work_day(date(2026, 6, 1)),
            _work_day(date(2026, 6, 2)),
            _work_day(date(2026, 6, 3)),
        ]
        self.assertEqual(list(EmployeeDaySchedule(days)), days)

    def test_add_to_days_no_overlap_is_ignored(self):
        day = _work_day(date(2026, 6, 1))
        schedule = EmployeeDaySchedule([day])
        schedule.add_to_days(
            datetime(2026, 6, 1, 7, 0),
            datetime(2026, 6, 1, 8, 0),
            "appointment",
            "Early meeting",
        )
        self.assertEqual(
            [ts for ts in day.day_schedule if ts.type == "appointment"], []
        )
        self.assertAlmostEqual(day.hours_appointment, 0.0)

    def test_add_to_days_within_work_adds_appointment(self):
        day = _work_day(date(2026, 6, 1))
        schedule = EmployeeDaySchedule([day])
        schedule.add_to_days(
            datetime(2026, 6, 1, 10, 0),
            datetime(2026, 6, 1, 11, 0),
            "appointment",
            "Team meeting",
        )
        appts = [ts for ts in day.day_schedule if ts.type == "appointment"]
        self.assertEqual(len(appts), 1)
        self.assertEqual(appts[0].start_time, time(10, 0))
        self.assertEqual(appts[0].end_time, time(11, 0))
        self.assertAlmostEqual(appts[0].hours_overlap_work, 1.0)
        self.assertAlmostEqual(day.hours_appointment, 1.0)

    def test_add_to_days_leave_requested_accumulates(self):
        day = _work_day(date(2026, 6, 1))
        schedule = EmployeeDaySchedule([day])
        schedule.add_to_days(
            datetime(2026, 6, 1, 10, 0),
            datetime(2026, 6, 1, 12, 0),
            "leave_requested",
            "Doctor",
        )
        self.assertAlmostEqual(day.hours_leave_requested, 2.0)
        self.assertAlmostEqual(day.hours_appointment, 0.0)

    def test_add_to_days_unknown_type_does_not_accumulate(self):
        """Unrecognised slot types are inserted but don't touch hours counters."""
        day = _work_day(date(2026, 6, 1))
        schedule = EmployeeDaySchedule([day])
        schedule.add_to_days(
            datetime(2026, 6, 1, 10, 0),
            datetime(2026, 6, 1, 11, 0),
            "other",
            "Something",
        )
        self.assertAlmostEqual(day.hours_leave_requested, 0.0)
        self.assertAlmostEqual(day.hours_appointment, 0.0)

    def test_add_to_days_date_not_in_schedule_is_ignored(self):
        day = _work_day(date(2026, 6, 1))
        schedule = EmployeeDaySchedule([day])
        schedule.add_to_days(
            datetime(2026, 6, 2, 10, 0),
            datetime(2026, 6, 2, 11, 0),
            "appointment",
            "Other day",
        )
        self.assertAlmostEqual(day.hours_appointment, 0.0)

    def test_add_to_days_multiday_slot_splits_across_days(self):
        """A multi-day slot contributes the correct overlap to each day."""
        mon = _work_day(date(2026, 6, 1))
        tue = _work_day(date(2026, 6, 2))
        schedule = EmployeeDaySchedule([mon, tue])
        # Mon 16:00 → Tue 11:00.
        schedule.add_to_days(
            datetime(2026, 6, 1, 16, 0),
            datetime(2026, 6, 2, 11, 0),
            "leave_requested",
            "Two-day leave",
        )
        self.assertAlmostEqual(mon.hours_leave_requested, 1.0)  # 16:00–17:00
        self.assertAlmostEqual(tue.hours_leave_requested, 2.0)  # 09:00–11:00

    def test_add_to_days_midnight_end_date_belongs_to_previous_day(self):
        """date_to with time 00:00 is treated as end-of-previous-day, not start-of-next."""
        mon = _work_day(date(2026, 6, 1))
        tue = _work_day(date(2026, 6, 2))
        schedule = EmployeeDaySchedule([mon, tue])
        # Slot ends exactly at midnight: should cover Mon only.
        schedule.add_to_days(
            datetime(2026, 6, 1, 16, 0),
            datetime(2026, 6, 2, 0, 0),
            "leave_requested",
            "Ends at midnight",
        )
        self.assertAlmostEqual(mon.hours_leave_requested, 1.0)
        self.assertAlmostEqual(tue.hours_leave_requested, 0.0)
