# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAllocationDomain(TransactionCase):
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
        cls.holiday_status = cls.env["hr.leave.type"].create(
            {
                "name": "Test Leave Type",
            }
        )

    def test_domain(self):
        action = (
            self.env["hr.leave.allocation.generate.multi.wizard"]
            .create(
                {
                    "holiday_status_id": self.holiday_status.id,
                    "allocation_mode": "domain",
                    "domain": [["id", "=", self.employee_01.id]],
                    "date_from": "2023-03-01",
                    "duration": 8,
                }
            )
            .action_generate_allocations()
        )
        allocations = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations.employee_id, self.employee_01)
