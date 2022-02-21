# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from freezegun import freeze_time

from odoo.tests.common import SavepointCase


class TestHours(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hour_obj = cls.env["hr.employee.hour"]
        cls.test_employee = cls.env["hr.employee"].create({"name": "Jacky"})
        cls.test_contract = cls.env["hr.contract"].create(
            {
                "name": "Test contract",
                "employee_id": cls.test_employee.id,
                "last_hours_report_date": "2022-02-01",
                "wage": 100,
            }
        )

    @freeze_time("2022-02-10")
    def test_contract_dates(self):
        self.assertEqual(
            self.test_employee.last_hours_report_date.strftime("%Y-%m-%d"), "2022-02-01"
        )
        self.hour_obj.action_generate_data(employee_ids=self.test_employee.ids)
        self.assertEqual(
            self.test_employee.last_hours_report_date.strftime("%Y-%m-%d"), "2022-02-10"
        )

    @freeze_time("2022-02-10")
    def test_create_hours_missing(self):
        self.hour_obj.action_generate_data(employee_ids=self.test_employee.ids)
        hours_missing = self.hour_obj.search(
            [("employee_id", "=", self.test_employee.id)]
        )
        # missing attendance from 01.02.2022 to 10.02.2022 created
        self.assertEqual(len(hours_missing), 7)
        self.assertEqual(sum(hours_missing.mapped("hours_qty")), -56)
