# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo.exceptions import ValidationError
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestHrHolidaysCredit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env["hr.employee"]
        cls.SudoEmployee = cls.Employee.sudo()
        cls.Department = cls.env["hr.department"]
        cls.SudoDepartment = cls.Department.sudo()

        cls.LeaveType = cls.env["hr.leave.type"]
        cls.SudoLeaveType = cls.LeaveType.sudo()
        cls.Leave = cls.env["hr.leave"]
        cls.SudoLeave = cls.Leave.sudo()
        cls.Allocation = cls.env["hr.leave.allocation"]
        cls.SudoAllocation = cls.Allocation.sudo()

    def test_1(self):
        """
        Test that creating a leave without allowing credit raises a
        ValidationError, and succeeds after enabling credit on the leave type.
        """
        employee = self.SudoEmployee.create({"name": "Employee #1"})
        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #1",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": False,
            }
        )

        allocation = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation.action_confirm()
        allocation.action_validate()

        with self.assertRaises(ValidationError):
            self.SudoLeave.create(
                {
                    "holiday_status_id": leave_type.id,
                    "holiday_type": "employee",
                    "employee_id": employee.id,
                    "date_from": "2020-01-01",
                    "date_to": "2020-01-10",
                }
            )

        leave_type.write({"allow_credit": True})
        self.SudoLeave.create(
            {
                "holiday_status_id": leave_type.id,
                "holiday_type": "employee",
                "employee_id": employee.id,
                "date_from": "2020-01-01",
                "date_to": "2020-01-10",
            }
        )

    def test_2(self):
        """
        Test that leave allocation validation respects department restrictions.
        Leaves for employees in allowed departments succeed, while others
        raise ValidationError.
        """
        department = self.SudoDepartment.create({"name": "Department #2"})
        employee_1 = self.SudoEmployee.create(
            {"name": "Employee #2-1", "department_id": department.id}
        )
        employee_2 = self.SudoEmployee.create(
            {"name": "Employee #2-2", "department_id": False}
        )

        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #2",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": True,
                "creditable_department_ids": [(6, False, [department.id])],
            }
        )

        allocation_1 = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee_1.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation_2 = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee_2.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )

        allocation_1.action_confirm()
        allocation_1.action_validate()
        allocation_2.action_confirm()
        allocation_2.action_validate()

        self.SudoLeave.create(
            {
                "holiday_status_id": leave_type.id,
                "holiday_type": "employee",
                "employee_id": employee_1.id,
                "number_of_days": 1,
            }
        )
        with self.assertRaises(ValidationError):
            self.SudoLeave.create(
                {
                    "holiday_status_id": leave_type.id,
                    "holiday_type": "employee",
                    "employee_id": employee_2.id,
                    "number_of_days": 1,
                }
            )

    def test_3(self):
        """
        Test that leave allocation validation respects individual employee
        credit restrictions. Leaves for employees with credit allowed succeed,
        while others raise ValidationError.
        """
        employee_1 = self.SudoEmployee.create({"name": "Employee #3-1"})
        employee_2 = self.SudoEmployee.create({"name": "Employee #3-2"})
        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #3",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": True,
                "creditable_employee_ids": [(6, False, [employee_1.id])],
            }
        )

        allocation_1 = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee_1.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation_2 = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee_2.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )

        allocation_1.action_confirm()
        allocation_1.action_validate()
        allocation_2.action_confirm()
        allocation_2.action_validate()

        self.SudoLeave.create(
            {
                "holiday_status_id": leave_type.id,
                "holiday_type": "employee",
                "employee_id": employee_1.id,
                "number_of_days": 1,
            }
        )
        with self.assertRaises(ValidationError):
            self.SudoLeave.create(
                {
                    "holiday_status_id": leave_type.id,
                    "holiday_type": "employee",
                    "employee_id": employee_2.id,
                    "number_of_days": 1,
                }
            )

    def test_4(self):
        """
        Test the name_get method
        """
        employee = self.SudoEmployee.create({"name": "Employee #4"})
        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #4",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": False,
            }
        )

        allocation = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation.action_confirm()
        allocation.action_validate()

        name = leave_type.with_context(employee_id=employee.id).name_get()[0][1]
        self.assertTrue("available" in name)
        self.assertTrue("credit" not in name)

    def test_5(self):
        """
        Test that the name_get method includes 'available + credit' in the
        leave type name when credit is allowed.
        """
        employee = self.SudoEmployee.create({"name": "Employee #5"})
        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #5",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": True,
            }
        )

        allocation = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation.action_confirm()
        allocation.action_validate()

        name = leave_type.with_context(employee_id=employee.id).name_get()[0][1]
        self.assertTrue("available + credit" in name)

    def test_6(self):
        """
        Test that the name_get method includes 'used in credit' in the leave
        type name when a leave consumes credit.
        """
        employee = self.SudoEmployee.create({"name": "Employee #6"})
        leave_type = self.SudoLeaveType.create(
            {
                "name": "Leave Type #6",
                "requires_allocation": "yes",
                "allocation_validation_type": "officer",
                "allow_credit": True,
            }
        )
        self.SudoLeave.create(
            {
                "holiday_status_id": leave_type.id,
                "holiday_type": "employee",
                "employee_id": employee.id,
                "number_of_days": 1,
            }
        )

        allocation = self.SudoAllocation.create(
            {
                "holiday_status_id": leave_type.id,
                "number_of_days": 5,
                "employee_id": employee.id,
                "date_from": "2020-01-01",
                "date_to": "2020-12-31",
            }
        )
        allocation.action_confirm()
        allocation.action_validate()

        name = leave_type.with_context(employee_id=employee.id).name_get()[0][1]
        self.assertTrue("used in credit" in name)
