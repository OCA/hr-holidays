# Copyright Dixmit 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command, Date
from odoo.tests.common import TransactionCase


class TestAllocationContractDateñ(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_01 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )
        cls.employee_02 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 2",
            }
        )
        cls.contract_01_01 = cls.env["hr.contract"].create(
            {
                "name": "Test Contract 01-01",
                "employee_id": cls.employee_01.id,
                "wage": 1500,
                "date_start": "2023-01-01",
            }
        )
        cls.contract_02_01 = cls.env["hr.contract"].create(
            {
                "name": "Test Contract 02-01",
                "employee_id": cls.employee_02.id,
                "wage": 1500,
                "date_start": "2023-06-01",
                "date_end": "2023-12-31",
            }
        )
        cls.contract_02_02 = cls.env["hr.contract"].create(
            {
                "name": "Test Contract 02-02",
                "employee_id": cls.employee_02.id,
                "wage": 1800,
                "date_start": "2024-01-01",
            }
        )
        cls.holiday_status = cls.env["hr.leave.type"].create(
            {
                "name": "Test Leave Type",
            }
        )
        cls.accural_plan = cls.env["hr.leave.accrual.plan"].create(
            {
                "name": "Test Accrual Plan",
                "accrued_gain_time": "start",
                "level_ids": [
                    Command.create(
                        {
                            "added_value": 2,
                            "start_count": 0,
                            "start_type": "year",
                        }
                    )
                ],
            }
        )

    def test_generation_no_check(self):
        action = (
            self.env["hr.leave.allocation.generate.multi.wizard"]
            .create(
                {
                    "holiday_status_id": self.holiday_status.id,
                    "allocation_mode": "employee",
                    "employee_ids": [
                        Command.set([self.employee_01.id, self.employee_02.id])
                    ],
                    "allocation_type": "accrual",
                    "accrual_plan_id": self.accural_plan.id,
                    "date_from": "2023-03-01",
                }
            )
            .action_generate_allocations()
        )
        allocations = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(allocations), 2)
        allocation_emp_01 = allocations.filtered(
            lambda a: a.employee_id == self.employee_01
        )
        allocation_emp_02 = allocations.filtered(
            lambda a: a.employee_id == self.employee_02
        )
        self.assertEqual(allocation_emp_01.date_from, Date.from_string("2023-03-01"))
        self.assertEqual(allocation_emp_02.date_from, Date.from_string("2023-03-01"))

    def test_generation_check(self):
        action = (
            self.env["hr.leave.allocation.generate.multi.wizard"]
            .create(
                {
                    "holiday_status_id": self.holiday_status.id,
                    "allocation_mode": "employee",
                    "employee_ids": [
                        Command.set([self.employee_01.id, self.employee_02.id])
                    ],
                    "allocation_type": "accrual",
                    "contract_date_enforce": True,
                    "accrual_plan_id": self.accural_plan.id,
                    "date_from": "2023-03-01",
                }
            )
            .action_generate_allocations()
        )
        allocations = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(allocations), 2)
        allocation_emp_01 = allocations.filtered(
            lambda a: a.employee_id == self.employee_01
        )
        allocation_emp_02 = allocations.filtered(
            lambda a: a.employee_id == self.employee_02
        )
        self.assertEqual(allocation_emp_01.date_from, Date.from_string("2023-03-01"))
        self.assertEqual(allocation_emp_02.date_from, Date.from_string("2023-06-01"))

    def test_generation_ignore_not_started(self):
        action = (
            self.env["hr.leave.allocation.generate.multi.wizard"]
            .create(
                {
                    "holiday_status_id": self.holiday_status.id,
                    "allocation_mode": "employee",
                    "employee_ids": [
                        Command.set([self.employee_01.id, self.employee_02.id])
                    ],
                    "allocation_type": "accrual",
                    "contract_date_enforce": True,
                    "accrual_plan_id": self.accural_plan.id,
                    "date_from": "2023-03-01",
                    "date_to": "2023-04-01",
                }
            )
            .action_generate_allocations()
        )
        allocations = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(allocations), 1)
        allocation_emp_01 = allocations.filtered(
            lambda a: a.employee_id == self.employee_01
        )
        self.assertEqual(allocation_emp_01.date_from, Date.from_string("2023-03-01"))
