from datetime import date

from odoo import Command
from odoo.tests.common import TransactionCase


class TestHrHolidaysAccrualsByTag(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.accrual_plan_model = cls.env["hr.leave.accrual.plan"]
        cls.leave_type_model = cls.env["hr.leave.type"]
        cls.accrual_allocation_model = cls.env["hr.leave.allocation"]
        cls.employee_categ_model = cls.env["hr.employee.category"]

        cls.accrual_plan1 = cls.accrual_plan_model.create(
            {"name": "Test Accrual Plan 1"}
        )
        cls.accrual_plan2 = cls.accrual_plan_model.create(
            {"name": "Test Accrual Plan 2"}
        )

        cls.leave_type = cls.leave_type_model.create(
            {"name": "Test Leave", "time_type": "leave"}
        )

        cls.tag1 = cls.employee_categ_model.create({"name": "Category 1"})
        cls.tag2 = cls.employee_categ_model.create({"name": "Category 2"})
        cls.tag3 = cls.employee_categ_model.create({"name": "Category 3"})

        cls.accrual_allocation_model.create(
            {
                "date_from": date.today(),
                "holiday_status_id": cls.leave_type.id,
                "holiday_type": "category",
                "accrual_plan_id": cls.accrual_plan1.id,
                "category_id": cls.tag1.id,
            }
        )
        cls.accrual_allocation_model.create(
            {
                "date_from": date.today(),
                "holiday_status_id": cls.leave_type.id,
                "holiday_type": "category",
                "accrual_plan_id": cls.accrual_plan2.id,
                "category_id": cls.tag2.id,
            }
        )

    def test_create_new_employee(self):
        # Employee without tags won't have any allocation
        employee1 = self.env["hr.employee"].create(
            {
                "name": "Test Employee 1",
                "company_id": self.company.id,
            }
        )
        allocations = self.accrual_allocation_model.search(
            [("employee_id", "=", employee1.id)]
        )
        self.assertFalse(allocations)

        # Creation of accrual allocation only with tags that have a related accrual plan
        employee2 = self.env["hr.employee"].create(
            {
                "name": "Test Employee 3",
                "company_id": self.company.id,
                "category_ids": [Command.set([self.tag1.id, self.tag3.id])],
            }
        )
        allocations = self.accrual_allocation_model.search(
            [("employee_id", "=", employee2.id)]
        )
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations.accrual_plan_id, self.accrual_plan1)

        # Adding a new tag with a related accrual plan
        employee2.category_ids = self.tag1 + self.tag2
        allocations = self.accrual_allocation_model.search(
            [("employee_id", "=", employee2.id)]
        )
        self.assertEqual(len(allocations), 2)
        self.assertFalse(any(allocation.date_to for allocation in allocations))

        # Updating tag list will update accrual allocations
        employee2.category_ids = self.tag2
        allocation1 = self.accrual_allocation_model.search(
            [
                ("employee_id", "=", employee2.id),
                ("accrual_plan_id", "=", self.accrual_plan1.id),
            ]
        )
        self.assertTrue(allocation1.date_to)
        allocation2 = self.accrual_allocation_model.search(
            [
                ("employee_id", "=", employee2.id),
                ("accrual_plan_id", "=", self.accrual_plan2.id),
            ]
        )
        self.assertFalse(allocation2.date_to)

        # Adding same tag again will create new accrual allocation
        employee2.category_ids = self.tag1 + self.tag2
        allocations = self.accrual_allocation_model.search(
            [
                ("employee_id", "=", employee2.id),
                ("accrual_plan_id", "=", self.accrual_plan1.id),
            ]
        )
        self.assertEqual(len(allocations), 2)
        self.assertFalse(all(allocation.date_to for allocation in allocations))
