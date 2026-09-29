# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from .common import TestHolidaysPublicResourceCommon


class TestReevaluate(TestHolidaysPublicResourceCommon):
    """A public holiday appearing over an approved leave has to adjust it.

    The adjustment itself is standard `_reevaluate_leaves`; what is asserted
    here is that generating the mirrors actually triggers it.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.friday = self.monday + timedelta(days=4)
        self.wednesday = self.monday + timedelta(days=2)
        self.leave = self._create_leave(self.employee, self.monday, self.friday)

    def test_a_leave_still_awaiting_approval_is_adapted_too(self):
        """A requested leave has to shrink as well, not only an approved one."""
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Needs Approval",
                "requires_allocation": False,
                "leave_validation_type": "hr",
                "request_unit": "day",
                "company_id": self.company.id,
            }
        )
        employee = self._create_employee("Emp Awaiting", self.calendar)
        leave = self._create_leave(
            employee, self.monday, self.friday, leave_type=leave_type
        )
        self.assertEqual(leave.state, "confirm", "the leave awaits approval")
        self.assertEqual(leave.number_of_days, 5)

        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(leave.number_of_days, 4)
        self.assertEqual(leave.state, "confirm", "it still awaits approval")

    def test_leave_is_validated(self):
        self.assertEqual(self.leave.state, "validate")
        self.assertEqual(self.leave.number_of_days, 5)

    def test_new_public_holiday_shortens_an_approved_leave(self):
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(self.leave.number_of_days, 4)

    def test_removing_the_public_holiday_restores_the_leave(self):
        line = self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(self.leave.number_of_days, 4)
        line.unlink()
        self.assertEqual(self.leave.number_of_days, 5)

    def test_moving_the_public_holiday_keeps_the_leave_consistent(self):
        line = self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(self.leave.number_of_days, 4)
        # Out of the leave period entirely.
        line.date = self.monday + timedelta(days=7)
        self.assertEqual(self.leave.number_of_days, 5)

    def test_new_regional_public_holiday_shortens_the_leave_of_its_person(self):
        """A personal record adjusts the leaves of its person, and only those.

        Standard only re-evaluates leaves for company-wide records; a
        regional public holiday is generated for one resource.
        """
        leave_by = self._create_leave(self.employee_by, self.monday, self.friday)
        self.assertEqual(leave_by.number_of_days, 5)
        self._create_line(self.wednesday, name="Fronleichnam", regions=self.region_by)
        self.assertEqual(leave_by.number_of_days, 4)
        self.assertEqual(leave_by.state, "validate")
        self.assertEqual(self.leave.number_of_days, 5, "not in the region")

    def test_removing_the_regional_public_holiday_restores_the_leave(self):
        leave_by = self._create_leave(self.employee_by, self.monday, self.friday)
        line = self._create_line(
            self.wednesday, name="Fronleichnam", regions=self.region_by
        )
        self.assertEqual(leave_by.number_of_days, 4)
        line.unlink()
        self.assertEqual(leave_by.number_of_days, 5)

    def test_moving_the_regional_public_holiday_keeps_the_leave_consistent(self):
        leave_by = self._create_leave(self.employee_by, self.monday, self.friday)
        line = self._create_line(
            self.wednesday, name="Fronleichnam", regions=self.region_by
        )
        self.assertEqual(leave_by.number_of_days, 4)
        line.date = self.monday + timedelta(days=7)
        self.assertEqual(leave_by.number_of_days, 5)

    def test_allocated_leave_is_refunded_and_notified(self):
        """Days taken from an allocation have to be given back, with a notice."""
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Allocated Time Off",
                "requires_allocation": True,
                "leave_validation_type": "no_validation",
                "allocation_validation_type": "no_validation",
                "request_unit": "day",
                "company_id": self.company.id,
            }
        )
        # A dedicated employee: self.employee is already off the whole week.
        employee = self._create_employee("Emp Allocated", self.calendar)
        allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Yearly allocation",
                "employee_id": employee.id,
                "holiday_status_id": leave_type.id,
                "number_of_days": 20,
                "date_from": self.monday,
            }
        )
        allocation.action_approve()
        leave = self._create_leave(
            employee, self.monday, self.friday, leave_type=leave_type
        )
        self.assertEqual(leave.number_of_days, 5)

        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertEqual(leave.number_of_days, 4)
        bodies = [str(body or "") for body in leave.message_ids.mapped("body")]
        self.assertTrue(
            any("global time off" in body for body in bodies),
            f"no notification about the change found in {bodies}",
        )
