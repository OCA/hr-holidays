# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime, time

from .common import WorkAndLeavesBase


class TestGetFullSchedulePerDay(WorkAndLeavesBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_user = cls.env["res.users"].create(
            {
                "name": "Employee User",
                "login": "employee_user@example.com",
                "email": "employee_user@example.com",
            }
        )
        cls.employee.write({"user_id": cls.employee_user.id})

    def _create_event(self, name, start, stop, privacy="public"):
        return self.env["calendar.event"].create(
            {
                "name": name,
                "start": start,
                "stop": stop,
                "privacy": privacy,
                "partner_ids": [(4, self.employee_user.partner_id.id)],
            }
        )

    def _full_schedule(self):
        """Return the full schedule for the week 2026-06-08 to 2026-06-12."""
        return self.employee._get_full_schedule_per_day(
            datetime(2026, 6, 8, 0, 0, 0),
            datetime(2026, 6, 12, 23, 59, 59),
        )

    def test_private_appointment_is_ignored(self):
        """A private calendar event must not appear in the schedule."""
        self._create_event(
            "Private Meeting",
            datetime(2026, 6, 10, 10, 0, 0),
            datetime(2026, 6, 10, 11, 0, 0),
            privacy="private",
        )
        result = self._full_schedule()
        wed = next(d for d in result if d.date == date(2026, 6, 10))
        self.assertEqual(
            [ts for ts in wed.day_schedule if ts.type == "appointment"], []
        )
        self.assertAlmostEqual(wed.hours_appointment, 0.0)

    def test_appointment_outside_work_is_ignored(self):
        """An appointment with no overlap with any work slot must not appear."""
        self._create_event(
            "After-hours Meeting",
            datetime(2026, 6, 10, 18, 0, 0),
            datetime(2026, 6, 10, 19, 0, 0),
        )
        result = self._full_schedule()
        wed = next(d for d in result if d.date == date(2026, 6, 10))
        self.assertEqual(
            [ts for ts in wed.day_schedule if ts.type == "appointment"], []
        )
        self.assertAlmostEqual(wed.hours_appointment, 0.0)

    def test_appointment_within_work(self):
        """An appointment entirely inside a work slot appears unclipped with full overlap."""
        self._create_event(
            "Team Meeting",
            datetime(2026, 6, 8, 10, 0, 0),
            datetime(2026, 6, 8, 11, 0, 0),
        )
        result = self._full_schedule()
        mon = next(d for d in result if d.date == date(2026, 6, 8))
        slots = [ts for ts in mon.day_schedule if ts.type == "appointment"]
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start_time, time(10, 0))
        self.assertEqual(slots[0].end_time, time(11, 0))
        self.assertAlmostEqual(slots[0].hours_overlap_work, 1.0)
        self.assertAlmostEqual(mon.hours_appointment, 1.0)

    def test_appointment_overlapping_work_start(self):
        """Appointment starting before work appears unclipped; overlap = work portion only."""
        self._create_event(
            "Early Meeting",
            datetime(2026, 6, 9, 8, 0, 0),
            datetime(2026, 6, 9, 10, 0, 0),
        )
        result = self._full_schedule()
        tue = next(d for d in result if d.date == date(2026, 6, 9))
        slots = [ts for ts in tue.day_schedule if ts.type == "appointment"]
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start_time, time(8, 0))
        self.assertEqual(slots[0].end_time, time(10, 0))
        self.assertAlmostEqual(slots[0].hours_overlap_work, 1.0)
        self.assertAlmostEqual(tue.hours_appointment, 1.0)

    def test_appointment_overlapping_work_end(self):
        """An appointment ending after work appears unclipped; overlap counts up to work end."""
        self._create_event(
            "Late Meeting",
            datetime(2026, 6, 11, 16, 0, 0),
            datetime(2026, 6, 11, 18, 0, 0),
        )
        result = self._full_schedule()
        thu = next(d for d in result if d.date == date(2026, 6, 11))
        slots = [ts for ts in thu.day_schedule if ts.type == "appointment"]
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start_time, time(16, 0))
        self.assertEqual(slots[0].end_time, time(18, 0))
        self.assertAlmostEqual(slots[0].hours_overlap_work, 1.0)
        self.assertAlmostEqual(thu.hours_appointment, 1.0)

    def test_requested_leave_outside_work_is_ignored(self):
        """A requested leave with no overlap with any work slot must not appear."""
        self._make_leave_request(
            self.employee,
            datetime(2026, 6, 10, 7, 0, 0),
            datetime(2026, 6, 10, 9, 0, 0),
            full_day=False,
        )
        result = self._full_schedule()
        wed = next(d for d in result if d.date == date(2026, 6, 10))
        self.assertEqual(
            [ts for ts in wed.day_schedule if ts.type == "leave_requested"], []
        )
        self.assertAlmostEqual(wed.hours_leave_requested, 0.0)

    def test_requested_leave_overlapping_work(self):
        """A requested leave starting before work appears unclipped; overlap is counted."""
        self._make_leave_request(
            self.employee,
            datetime(2026, 6, 8, 7, 0, 0),
            datetime(2026, 6, 8, 11, 0, 0),
            full_day=False,
        )
        result = self._full_schedule()
        mon = next(d for d in result if d.date == date(2026, 6, 8))
        slots = [ts for ts in mon.day_schedule if ts.type == "leave_requested"]
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start_time, time(7, 0))
        self.assertEqual(slots[0].end_time, time(11, 0))
        self.assertAlmostEqual(slots[0].hours_overlap_work, 2.0)
        self.assertAlmostEqual(mon.hours_leave_requested, 2.0)
