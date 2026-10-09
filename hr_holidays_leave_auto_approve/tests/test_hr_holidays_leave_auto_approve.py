# Copyright 2016-2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.addons.base.tests.common import BaseCommon


class TestHolidaysAutoValidate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_model = cls.env["hr.employee"]
        cls.user_model = cls.env["res.users"]
        cls.leave_type_model = cls.env["hr.leave.type"]
        cls.leave_request_model = cls.env["hr.leave"]
        cls.leave_allocation_model = cls.env["hr.leave.allocation"]

        # Create an employee user to make leave requests
        cls.test_user_id = cls.user_model.create(
            {"name": "Test User", "login": "test_user", "email": "mymail@test.com"}
        )

        # Create an employee related to the user to make leave requests
        cls.test_employee_id = cls.employee_model.create(
            {"name": "Test Employee", "user_id": cls.test_user_id.id}
        )

        # Create 2 leave type
        cls.test_leave_type1_id = cls.leave_type_model.create(
            {"name": "Test Leave Type1", "auto_approve_policy": "hr"}
        )
        cls.test_leave_type2_id = cls.leave_type_model.create(
            {"name": "Test Leave Type2", "auto_approve_policy": "no"}
        )

        # Create leave allocation requests for Test Leave Type1 and 2
        cls.leave_allocation1 = cls.leave_allocation_model.create(
            {
                "name": "Test Allocation Request 1",
                "holiday_status_id": cls.test_leave_type1_id.id,
                "holiday_type": "employee",
                "employee_id": cls.test_employee_id.id,
                "number_of_days": 10,
            }
        )

        cls.leave_allocation2 = cls.leave_allocation_model.create(
            {
                "name": "Test Allocation Request 2",
                "holiday_status_id": cls.test_leave_type2_id.id,
                "holiday_type": "employee",
                "employee_id": cls.test_employee_id.id,
                "number_of_days": 10,
            }
        )

    def test_allocation_requests_state(self):
        # Check for leave_allocation1 state
        self.assertEqual(self.leave_allocation1.state, "validate")

        # Check for leave_allocation2 state
        self.assertEqual(self.leave_allocation2.state, "validate")

    def test_leave_requests_state(self):
        today = datetime.today()

        # Create leave requests for Leave Type1 and 2
        leave1 = self.leave_request_model.create(
            {
                "name": "Test Leave Request 1",
                "holiday_status_id": self.test_leave_type1_id.id,
                "date_from": today,
                "date_to": today + timedelta(days=1),
                "holiday_type": "employee",
                "employee_id": self.test_employee_id.id,
            }
        )

        leave2 = self.leave_request_model.create(
            {
                "name": "Test Leave Request 2",
                "holiday_status_id": self.test_leave_type2_id.id,
                "date_from": today + timedelta(days=5),
                "date_to": today + timedelta(days=8),
                "holiday_type": "employee",
                "employee_id": self.test_employee_id.id,
            }
        )

        # Check for leave1 state
        self.assertEqual(leave1.state, "validate")

        # Check for leave2 state
        self.assertEqual(leave2.state, "confirm")

    def test_leave_requests_state_employee_user(self):
        today = datetime.today()

        # Create leave requests for Leave Type1 and 2
        leave1 = self.leave_request_model.with_user(self.test_user_id).create(
            {
                "name": "Test Leave Request 1",
                "holiday_status_id": self.test_leave_type1_id.id,
                "date_from": today + timedelta(days=10),
                "date_to": today + timedelta(days=12),
                "holiday_type": "employee",
                "employee_id": self.test_employee_id.id,
            }
        )

        leave2 = self.leave_request_model.with_user(self.test_user_id).create(
            {
                "name": "Test Leave Request 2",
                "holiday_status_id": self.test_leave_type2_id.id,
                "holiday_type": "employee",
                "date_from": today + timedelta(days=13),
                "date_to": today + timedelta(days=14),
                "employee_id": self.test_employee_id.id,
            }
        )

        # Check for leave1 state
        self.assertEqual(leave1.state, "validate")

        # Check for leave2 state
        self.assertEqual(leave2.state, "confirm")

    def test_leave_request_employee_validate_all(self):
        self.test_user_id.groups_id = [(6, 0, [self.env.ref("base.group_user").id])]

        today = datetime.today()
        self.test_leave_type2_id.write({"auto_approve_policy": "all"})

        leave1 = self.leave_request_model.with_user(self.test_user_id).create(
            {
                "name": "Test Leave Request 1",
                "holiday_status_id": self.test_leave_type1_id.id,
                "date_from": today + timedelta(days=10),
                "date_to": today + timedelta(days=12),
                "holiday_type": "employee",
                "employee_id": self.test_employee_id.id,
            }
        )

        leave2 = self.leave_request_model.with_user(self.test_user_id).create(
            {
                "name": "Test Leave Request 2",
                "holiday_status_id": self.test_leave_type2_id.id,
                "holiday_type": "employee",
                "date_from": today + timedelta(days=13),
                "date_to": today + timedelta(days=14),
                "employee_id": self.test_employee_id.id,
            }
        )

        # Check for leave1 state
        self.assertEqual(leave1.state, "confirm")

        # Check for leave2 state
        self.assertEqual(leave2.state, "validate")
