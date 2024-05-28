# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime

import odoo.tests.common as common
from odoo.exceptions import UserError


class TestHrLeave(common.TransactionCase):
    def setUp(self):
        super().setUp()
        employee = self.env["hr.employee"].search([])[0]
        employee.write({"leave_manager_ids": [(6, 0, [6, 2])]})
        hr_leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Leave Test",
                "color_name": "red",
                "request_unit": "hour",
            }
        )
        self.hr_leave = self.env["hr.leave"].create(
            {
                "employee_id": employee.id,
                "holiday_status_id": hr_leave_type.id,
                "holiday_type": "employee",
                "date_from": datetime(year=2023, month=10, day=1, hour=8, minute=0),
                "date_to": datetime(year=2023, month=10, day=3, hour=8, minute=0),
            }
        )

        self.user1 = self.env["res.users"].create(
            {
                "name": "User 1",
                "login": "user1",
                "password": "password1",
                "groups_id": [],
            }
        )

    def test_hr_leave_managers_can_validate_leaves(self):
        """Test that checks if all leave managers in field leave_manager_ids can
        confirm a hr_leave and hr_leave_allocations"""
        self.env.user = self.env["res.users"].browse(6)
        self.hr_leave.with_user(self.env.user).action_validate()
        self.assertEqual(self.hr_leave.state, "validate")
        self.hr_leave.state = "confirm"
        self.env.user = self.env["res.users"].browse(2)
        self.hr_leave.with_user(self.env.user).action_validate()
        self.assertEqual(self.hr_leave.state, "validate")
        self.hr_leave.state = "confirm"

        # remove user with id 2 from manager groups
        approver_group = self.env.ref(
            "hr_holidays.group_hr_holidays_manager", raise_if_not_found=False
        )
        other_group = self.env.ref(
            "hr_holidays.group_hr_holidays_user", raise_if_not_found=False
        )
        if approver_group:
            approver_group.sudo().write({"users": [(3, 2)]})
            other_group.sudo().write({"users": [(3, 2)]})

        # checks that trying to validate leaves with no rights raises an error
        with self.assertRaises(UserError):
            self.hr_leave.with_user(self.user1)._check_approval_update("validate")
