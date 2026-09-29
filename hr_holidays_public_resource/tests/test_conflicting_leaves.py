# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError

from .common import TestHolidaysPublicResourceCommon


class TestConflictingLeaves(TestHolidaysPublicResourceCommon):
    """A conflict already in the data must not block the configuration.

    Standard raises "An employee already booked time off which overlaps with
    this period" whenever a leave is written while another of the same employee
    overlaps it. The synchronisation makes standard recompute exactly those
    leaves, so without care every public holiday and every working schedule
    became unsaveable as soon as one employee somewhere had two overlapping
    requests.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Needs Approval",
                "requires_allocation": False,
                "leave_validation_type": "hr",
                "request_unit": "day",
                "allow_request_on_top": False,
                "company_id": self.company.id,
            }
        )
        # Standard would refuse to create the second one, so the overlap is
        # planted the way a real database ends up with one.
        skip = {"leave_skip_date_check": True}
        self.first = (
            self.env["hr.leave"]
            .with_context(**skip)
            .create(
                {
                    "name": "Whole week",
                    "employee_id": self.employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": self.monday,
                    "request_date_to": self.monday + timedelta(days=4),
                }
            )
        )
        self.second = (
            self.env["hr.leave"]
            .with_context(**skip)
            .create(
                {
                    "name": "Two days inside it",
                    "employee_id": self.employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": self.monday + timedelta(days=1),
                    "request_date_to": self.wednesday,
                }
            )
        )
        self.assertTrue(self.first.dashboard_warning_message)

    def _manual_public_holiday(self):
        return self.leave_model.create(
            {
                "name": "Entered by hand",
                "calendar_id": self.calendar.id,
                "date_from": datetime(
                    self.wednesday.year, self.wednesday.month, self.wednesday.day, 0, 0
                ),
                "date_to": datetime(
                    self.wednesday.year,
                    self.wednesday.month,
                    self.wednesday.day,
                    23,
                    59,
                    59,
                ),
            }
        )

    def test_a_hand_made_public_holiday_can_still_be_created(self):
        self.assertTrue(self._manual_public_holiday().exists())

    def test_a_hand_made_public_holiday_can_still_be_deleted(self):
        manual = self._manual_public_holiday()
        self.assertFalse(manual.public_holiday_line_id, "nothing generated it")
        manual.unlink()
        self.assertFalse(manual.exists())

    def test_a_hand_made_public_holiday_can_still_be_moved(self):
        manual = self._manual_public_holiday()
        manual.name = "Renamed by hand"
        self.assertEqual(manual.name, "Renamed by hand")

    def test_a_public_holiday_can_still_be_created(self):
        line = self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertTrue(line.global_leave_ids)

    def test_a_working_schedule_can_still_be_saved(self):
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.calendar.public_holiday_employee_sync = False
        self.calendar.public_holiday_employee_sync = True
        self.assertTrue(self.calendar.public_holiday_employee_sync)

    def test_a_public_holiday_can_still_be_removed(self):
        line = self._create_line(self.wednesday, name="Mid-week holiday")
        line.unlink()
        self.assertFalse(line.exists())

    def test_the_conflicting_leaves_are_still_recomputed(self):
        self.assertEqual(self.first.number_of_days, 5)
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(
            self.first.number_of_days, 4, "the holiday still shortens the leave"
        )

    def test_a_genuine_overlap_is_still_refused_for_users(self):
        """Skipping the check must not leak outside the synchronisation."""
        self._create_line(self.wednesday, name="Mid-week holiday")
        leave_type = self.first.holiday_status_id
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "name": "Yet another",
                    "employee_id": self.employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": self.monday,
                    "request_date_to": self.monday,
                }
            )
