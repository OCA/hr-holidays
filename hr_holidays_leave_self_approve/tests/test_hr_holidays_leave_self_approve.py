# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestHolidaysAutoValidate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.employee_model = cls.env["hr.employee"]
        cls.user_model = cls.env["res.users"]
        cls.leave_request_model = cls.env["hr.leave"]
        cls.leave_allocation_model = cls.env["hr.leave.allocation"]

        # Create an employee user to make leave requests
        cls.test_user_id = cls.user_model.create(
            {"name": "Test User", "login": "test_user", "email": "mymail@test.com"}
        )

        # Create an employee related to the user to make leave requests
        # Assign user as self-approver
        cls.test_employee_id = cls.employee_model.create(
            {
                "name": "Test Employee",
                "user_id": cls.test_user_id.id,
                "leave_manager_id": cls.test_user_id.id,
            }
        )

        # "Paid Leave" type
        leave_type = cls.env.ref("hr_holidays.holiday_status_cl")

        # Create leave allocation request
        cls.leave_allocation = cls.leave_allocation_model.create(
            {
                "name": "Test Allocation Request",
                "holiday_status_id": leave_type.id,
                "holiday_type": "employee",
                "employee_id": cls.test_employee_id.id,
                "number_of_days": 10,
            }
        )

    def test_allocation_request_state(self):
        # Check for leave_allocation state
        self.assertEqual(self.leave_allocation.state, "draft")

        # Validate the leave_allocation
        self.leave_allocation.action_confirm()
        self.leave_allocation.action_validate()

        # Check for leave_allocation state
        self.assertEqual(self.leave_allocation.state, "validate")

    def test_leave_request_state(self):
        today = datetime.today()

        # Create leave request
        leave = self.leave_request_model.create(
            {
                "name": "Test Leave Request",
                "holiday_status_id": self.leave_allocation.holiday_status_id.id,
                "date_from": today,
                "date_to": today + timedelta(days=2),
                "holiday_type": "employee",
                "employee_id": self.test_employee_id.id,
            }
        )

        # Check for leave "To approve"
        self.assertEqual(leave.state, "confirm")

        # Self approve
        leave.with_user(self.test_user_id).action_approve()

        # Check for leave state "Approved"
        self.assertEqual(leave.state, "validate1")
