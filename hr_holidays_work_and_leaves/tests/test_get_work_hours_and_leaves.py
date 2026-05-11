# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime, time

from .common import WorkAndLeavesBase


class TestGetWorkHoursAndLeaves(WorkAndLeavesBase):
    def test_five_day_week_with_full_and_partial_leave(self):
        """Even week (5 days): full Mon leave + Fri half-day leave → 2 leave, 5 work."""
        # ISO week 20 (even, week_type 0): Mon–Fri all working.
        # Full-day leave Monday 2026-05-11.
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 11, 9, 0, 0),
            datetime(2026, 5, 11, 17, 0, 0),
        )
        # Half-day leave Friday 2026-05-15 11:00–13:00.
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 15, 11, 0, 0),
            datetime(2026, 5, 15, 13, 0, 0),
            full_day=False,
        )
        start_datetime = datetime(2026, 5, 11, 7, 0, 0)
        end_datetime = datetime(2026, 5, 15, 18, 0, 0)

        result = self.employee_two_week._get_work_hours_and_leaves(
            start_datetime, end_datetime
        )

        leave_entries = [e for e in result if e.type == "leave"]
        work_entries = [e for e in result if e.type == "work"]
        self.assertEqual(len(leave_entries), 2)
        self.assertEqual(len(work_entries), 5)
        # Monday: only leave, no work.
        monday_entries = [e for e in result if e.datetime_from.date().day == 11]
        self.assertEqual(len(monday_entries), 1)
        self.assertEqual(monday_entries[0].type, "leave")
        # Friday: two work slots split around the half-day leave.
        friday_entries = [e for e in result if e.datetime_from.date().day == 15]
        friday_work = [e for e in friday_entries if e.type == "work"]
        self.assertEqual(len(friday_work), 2)
        self.assertEqual(
            friday_work[0].datetime_from.timetz().replace(tzinfo=None), time(9, 0)
        )
        self.assertEqual(
            friday_work[0].datetime_to.timetz().replace(tzinfo=None), time(11, 0)
        )
        self.assertEqual(
            friday_work[1].datetime_from.timetz().replace(tzinfo=None), time(13, 0)
        )
        self.assertEqual(
            friday_work[1].datetime_to.timetz().replace(tzinfo=None), time(17, 0)
        )

    def test_four_day_week_with_spanning_leave(self):
        """Odd week (4 days, Mon off): leave from prev Fri to Wed → 2 leave, 2 work."""
        # ISO week 21 (odd, week_type 1): Mon off, Tue–Fri working.
        # Leave from Friday 2026-05-15 09:00 through Wednesday 2026-05-20 17:00.
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 15, 9, 0, 0),
            datetime(2026, 5, 20, 17, 0, 0),
        )
        # Period: Mon 2026-05-18 through Fri 2026-05-22.
        start_datetime = datetime(2026, 5, 18, 7, 0, 0)
        end_datetime = datetime(2026, 5, 22, 18, 0, 0)

        result = self.employee_two_week._get_work_hours_and_leaves(
            start_datetime, end_datetime
        )

        # Monday is a day off in the odd week, so not present at all.
        monday_entries = [e for e in result if e.datetime_from.date().day == 18]
        self.assertEqual(len(monday_entries), 0)
        leave_entries = [e for e in result if e.type == "leave"]
        work_entries = [e for e in result if e.type == "work"]
        self.assertEqual(len(leave_entries), 2)
        self.assertEqual(len(work_entries), 2)
        # Leave entries cover Tuesday and Wednesday (clipped to work hours).
        self.assertEqual(leave_entries[0].datetime_from.date().day, 19)  # Tue
        self.assertEqual(leave_entries[1].datetime_from.date().day, 20)  # Wed
        # Work entries are Thursday and Friday.
        self.assertEqual(work_entries[0].datetime_from.date().day, 21)  # Thu
        self.assertEqual(work_entries[1].datetime_from.date().day, 22)  # Fri

    def test_five_day_week_with_holiday_splitting_leave(self):
        """Mon-Fri week: leave Tue-Thu with holiday on Wed → work,leave,holiday,leave,work."""
        # Public holiday: Wednesday 2026-05-27.
        self._make_public_holiday(date(2026, 5, 27))
        # Leave from Tuesday 09:00 through Thursday 17:00 (spans the holiday).
        self._make_validated_leave(
            self.employee,
            datetime(2026, 5, 26, 9, 0, 0),
            datetime(2026, 5, 28, 17, 0, 0),
        )
        start_datetime = datetime(2026, 5, 25, 7, 0, 0)
        end_datetime = datetime(2026, 5, 29, 18, 0, 0)

        result = self.employee._get_work_hours_and_leaves(start_datetime, end_datetime)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0].type, "work")
        self.assertEqual(result[0].datetime_from.date().day, 25)  # Mon
        self.assertEqual(result[1].type, "leave")
        self.assertEqual(result[1].datetime_from.date().day, 26)  # Tue
        self.assertEqual(result[2].type, "holiday")
        self.assertEqual(result[2].datetime_from.date().day, 27)  # Wed
        self.assertEqual(result[3].type, "leave")
        self.assertEqual(result[3].datetime_from.date().day, 28)  # Thu
        self.assertEqual(result[4].type, "work")
        self.assertEqual(result[4].datetime_from.date().day, 29)  # Fri

    def test_four_day_week_with_holiday_and_partial_leave(self):
        """Odd week (Mon off): holiday Thu, 4h leave Fri 09-13 →
        Tue/Wed work, Thu holiday, Fri×2.
        """
        # Public holiday: Thursday 2026-05-21 (week 21, odd week for two-week calendar).
        self._make_public_holiday(date(2026, 5, 21))
        # Half-day leave Friday 2026-05-22 09:00–13:00.
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 22, 9, 0, 0),
            datetime(2026, 5, 22, 13, 0, 0),
            full_day=False,
        )
        start_datetime = datetime(2026, 5, 18, 7, 0, 0)
        end_datetime = datetime(2026, 5, 22, 18, 0, 0)

        result = self.employee_two_week._get_work_hours_and_leaves(
            start_datetime, end_datetime
        )

        self.assertEqual(len(result), 5)
        # Monday is a day off in the odd week.
        monday_entries = [e for e in result if e.datetime_from.date().day == 18]
        self.assertEqual(len(monday_entries), 0)
        # Tuesday and Wednesday: full work days.
        self.assertEqual(result[0].type, "work")
        self.assertEqual(result[0].datetime_from.date().day, 19)  # Tue
        self.assertEqual(result[1].type, "work")
        self.assertEqual(result[1].datetime_from.date().day, 20)  # Wed
        # Thursday: replaced by the public holiday.
        self.assertEqual(result[2].type, "holiday")
        self.assertEqual(result[2].datetime_from.date().day, 21)  # Thu
        # Friday: leave 09-13, then remaining work 13-17.
        self.assertEqual(result[3].type, "leave")
        self.assertEqual(result[3].datetime_from.date().day, 22)  # Fri
        self.assertEqual(
            result[3].datetime_from.timetz().replace(tzinfo=None), time(9, 0)
        )
        self.assertEqual(
            result[3].datetime_to.timetz().replace(tzinfo=None), time(13, 0)
        )
        self.assertEqual(result[4].type, "work")
        self.assertEqual(result[4].datetime_from.date().day, 22)  # Fri
        self.assertEqual(
            result[4].datetime_from.timetz().replace(tzinfo=None), time(13, 0)
        )
        self.assertEqual(
            result[4].datetime_to.timetz().replace(tzinfo=None), time(17, 0)
        )

    def test_leave_starting_before_work_schedule(self):
        """Leave starting before 09:00 is clipped to work start; remaining work follows."""
        # Leave Tuesday 2026-06-02 07:00–13:00 — starts 2 h before work begins.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 7, 0, 0),
            datetime(2026, 6, 2, 13, 0, 0),
            full_day=False,
        )
        start_datetime = datetime(2026, 6, 1, 7, 0, 0)
        end_datetime = datetime(2026, 6, 5, 18, 0, 0)

        result = self.employee._get_work_hours_and_leaves(start_datetime, end_datetime)

        tuesday = [e for e in result if e.datetime_from.date().day == 2]
        self.assertEqual(len(tuesday), 2)
        leave_slot = next(e for e in tuesday if e.type == "leave")
        work_slot = next(e for e in tuesday if e.type == "work")
        # Leave is clipped to work start.
        self.assertEqual(
            leave_slot.datetime_from.timetz().replace(tzinfo=None), time(9, 0)
        )
        self.assertEqual(
            leave_slot.datetime_to.timetz().replace(tzinfo=None), time(13, 0)
        )
        # Remaining work runs from leave end to work end.
        self.assertEqual(
            work_slot.datetime_from.timetz().replace(tzinfo=None), time(13, 0)
        )
        self.assertEqual(
            work_slot.datetime_to.timetz().replace(tzinfo=None), time(17, 0)
        )

    def test_leave_ending_after_work_schedule(self):
        """Leave ending after 17:00 is clipped to work end; preceding work is emitted."""
        # Leave Tuesday 2026-06-02 13:00–19:00 — ends 2 h after work finishes.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 13, 0, 0),
            datetime(2026, 6, 2, 19, 0, 0),
            full_day=False,
        )
        start_datetime = datetime(2026, 6, 1, 7, 0, 0)
        end_datetime = datetime(2026, 6, 5, 18, 0, 0)

        result = self.employee._get_work_hours_and_leaves(start_datetime, end_datetime)

        tuesday = [e for e in result if e.datetime_from.date().day == 2]
        self.assertEqual(len(tuesday), 2)
        work_slot = next(e for e in tuesday if e.type == "work")
        leave_slot = next(e for e in tuesday if e.type == "leave")
        # Work runs from work start to leave start.
        self.assertEqual(
            work_slot.datetime_from.timetz().replace(tzinfo=None), time(9, 0)
        )
        self.assertEqual(
            work_slot.datetime_to.timetz().replace(tzinfo=None), time(13, 0)
        )
        # Leave is clipped to work end.
        self.assertEqual(
            leave_slot.datetime_from.timetz().replace(tzinfo=None), time(13, 0)
        )
        self.assertEqual(
            leave_slot.datetime_to.timetz().replace(tzinfo=None), time(17, 0)
        )

    def test_two_leaves_within_one_work_slot(self):
        """Two partial leaves within a single work slot produce five entries."""
        # Leave 1: 10:00–11:00, Leave 2: 13:00–14:00, both on Tuesday 2026-06-02.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 10, 0, 0),
            datetime(2026, 6, 2, 11, 0, 0),
            full_day=False,
        )
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 13, 0, 0),
            datetime(2026, 6, 2, 14, 0, 0),
            full_day=False,
        )
        result = self.employee._get_work_hours_and_leaves(
            datetime(2026, 6, 2, 7, 0, 0),
            datetime(2026, 6, 2, 18, 0, 0),
        )
        tuesday = [e for e in result if e.datetime_from.date().day == 2]
        self.assertEqual(len(tuesday), 5)
        types = [e.type for e in tuesday]
        self.assertEqual(types, ["work", "leave", "work", "leave", "work"])
        times = [(e.datetime_from.hour, e.datetime_to.hour) for e in tuesday]
        self.assertEqual(times, [(9, 10), (10, 11), (11, 13), (13, 14), (14, 17)])

    def test_three_leaves_within_one_work_slot(self):
        """Three partial leaves within a single work slot produce seven entries."""
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 10, 0, 0),
            datetime(2026, 6, 2, 11, 0, 0),
            full_day=False,
        )
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 12, 0, 0),
            datetime(2026, 6, 2, 13, 0, 0),
            full_day=False,
        )
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 15, 0, 0),
            datetime(2026, 6, 2, 16, 0, 0),
            full_day=False,
        )
        result = self.employee._get_work_hours_and_leaves(
            datetime(2026, 6, 2, 7, 0, 0),
            datetime(2026, 6, 2, 18, 0, 0),
        )
        tuesday = [e for e in result if e.datetime_from.date().day == 2]
        self.assertEqual(len(tuesday), 7)
        types = [e.type for e in tuesday]
        self.assertEqual(
            types, ["work", "leave", "work", "leave", "work", "leave", "work"]
        )
        times = [(e.datetime_from.hour, e.datetime_to.hour) for e in tuesday]
        self.assertEqual(
            times, [(9, 10), (10, 11), (11, 12), (12, 13), (13, 15), (15, 16), (16, 17)]
        )

    def test_leave_before_work_then_second_leave_within_remaining_work(self):
        """Leave starting before work then a second leave within the remaining work slot."""
        # Leave 1: 07:00–11:00 (starts before work at 09:00).
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 7, 0, 0),
            datetime(2026, 6, 2, 11, 0, 0),
            full_day=False,
        )
        # Leave 2: 13:00–14:00 (within remaining work 11:00–17:00).
        self._make_validated_leave(
            self.employee,
            datetime(2026, 6, 2, 13, 0, 0),
            datetime(2026, 6, 2, 14, 0, 0),
            full_day=False,
        )
        result = self.employee._get_work_hours_and_leaves(
            datetime(2026, 6, 2, 7, 0, 0),
            datetime(2026, 6, 2, 18, 0, 0),
        )
        tuesday = [e for e in result if e.datetime_from.date().day == 2]
        self.assertEqual(len(tuesday), 4)
        types = [e.type for e in tuesday]
        self.assertEqual(types, ["leave", "work", "leave", "work"])
        times = [(e.datetime_from.hour, e.datetime_to.hour) for e in tuesday]
        self.assertEqual(times, [(9, 11), (11, 13), (13, 14), (14, 17)])

    def test_full_day_leave_adjusts_to_changed_work_schedule(self):
        """Full-day leave is clipped to the current schedule, not the stored leave times."""
        # Register a full-day leave while the schedule is 09:00–17:00.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 5, 11, 9, 0, 0),
            datetime(2026, 5, 11, 17, 0, 0),
        )
        # Simulate a schedule change: shift all attendances to 08:00–16:00.
        self.employee.resource_calendar_id.attendance_ids.write(
            {"hour_from": 8.0, "hour_to": 16.0}
        )

        result = self.employee._get_work_hours_and_leaves(
            datetime(2026, 5, 11, 7, 0, 0),
            datetime(2026, 5, 11, 18, 0, 0),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "leave")
        self.assertEqual(
            result[0].datetime_from.timetz().replace(tzinfo=None), time(8, 0)
        )
        self.assertEqual(
            result[0].datetime_to.timetz().replace(tzinfo=None), time(16, 0)
        )
        self.assertAlmostEqual(result[0].duration, 8.0)
