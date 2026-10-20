# Copyright 2026 Antoni Marroig (APSL-Nagarro) <antoni.marroig@nagarro.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestManagerHierarchy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        Employee = cls.env["hr.employee"]
        cls.user_top = new_test_user(
            cls.env,
            login="hierarchy_top",
            groups="base.group_user,hr_holidays.group_hr_holidays_responsible",
        )
        cls.user_outsider = new_test_user(
            cls.env, login="hierarchy_outsider", groups="base.group_user"
        )
        cls.top = Employee.create({"name": "Top", "user_id": cls.user_top.id})
        # Middle manager without user: the top manager is not the direct
        # approver of the bottom employee.
        cls.middle = Employee.create({"name": "Middle", "parent_id": cls.top.id})
        cls.bottom = Employee.create({"name": "Bottom", "parent_id": cls.middle.id})
        cls.outsider = Employee.create(
            {"name": "Outsider", "user_id": cls.user_outsider.id}
        )

    def _create_leaves(self, validation_type="manager"):
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Hierarchy Leave",
                "requires_allocation": "no",
                "leave_validation_type": validation_type,
            }
        )
        return self.env["hr.leave"].create(
            [
                {
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": f"2026-11-0{day}",
                    "request_date_to": f"2026-11-0{day}",
                }
                for day, employee in enumerate(
                    (self.middle, self.bottom, self.outsider), start=2
                )
            ]
        )

    def _as_top(self, records, employee):
        return records.filtered(lambda r: r.employee_id == employee).with_user(
            self.user_top
        )

    def test_01_read_leaves(self):
        leaves = self._create_leaves()
        self.assertNotEqual(self.bottom.leave_manager_id, self.user_top)
        visible = (
            self.env["hr.leave"]
            .with_user(self.user_top)
            .search([("id", "in", leaves.ids)])
        )
        self.assertEqual(visible.employee_id, self.middle | self.bottom)

    def test_02_hierarchy_filter(self):
        leaves = self._create_leaves()
        team_leaves = (
            self.env["hr.leave"]
            .with_user(self.user_top)
            .search([("id", "in", leaves.ids), ("in_manager_hierarchy", "=", True)])
        )
        self.assertEqual(team_leaves.employee_id, self.middle | self.bottom)
        other_leaves = (
            self.env["hr.leave"]
            .with_user(self.user_top)
            .search([("id", "in", leaves.ids), ("in_manager_hierarchy", "=", False)])
        )
        self.assertFalse(other_leaves)

    def test_03_approve_and_refuse_leaves(self):
        leaves = self._create_leaves()
        bottom_leave = self._as_top(leaves, self.bottom)
        self.assertTrue(bottom_leave.can_approve)
        bottom_leave.action_approve()
        self.assertEqual(bottom_leave.state, "validate")
        middle_leave = self._as_top(leaves, self.middle)
        middle_leave.action_refuse()
        self.assertEqual(middle_leave.state, "refuse")
        with self.assertRaises(AccessError):
            self._as_top(leaves, self.outsider).action_approve()

    def test_04_cannot_approve_officer_validation(self):
        leaves = self._create_leaves(validation_type="hr")
        bottom_leave = self._as_top(leaves, self.bottom)
        self.assertFalse(bottom_leave.can_approve)
        with self.assertRaises(UserError):
            bottom_leave.action_approve()

    def test_05_first_approval_double_validation(self):
        leaves = self._create_leaves(validation_type="both")
        bottom_leave = self._as_top(leaves, self.bottom)
        self.assertTrue(bottom_leave.can_approve)
        bottom_leave.action_approve()
        self.assertEqual(bottom_leave.state, "validate1")
        with self.assertRaises(AccessError):
            self._as_top(leaves, self.outsider).action_approve()
