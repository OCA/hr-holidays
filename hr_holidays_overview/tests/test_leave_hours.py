# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

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
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Legal Leaves",
                "time_type": "leave",
                "allocation_type": "no",
                "validity_start": False,
            }
        )

    @freeze_time("2022-02-10")
    def test_create_leave(self):
        start = datetime(2022, 2, 3, 8, 0, 0)
        end = datetime(2022, 2, 3, 19, 0, 0)
        self.env["hr.leave"].create(
            {
                "name": "1leave",
                "employee_id": self.test_employee.id,
                "holiday_status_id": self.leave_type.id,
                "date_from": start,
                "date_to": end,
                "number_of_days": 1,
            }
        )
        self.hour_obj.action_generate_data(employee_ids=self.test_employee.ids)
        leave_request_hours = self.hour_obj.search(
            [
                ("employee_id", "=", self.test_employee.id),
                ("type", "=", "leave_request"),
            ]
        )
        self.assertEqual(len(leave_request_hours), 1)
        self.assertEqual(leave_request_hours.days_qty, 1)

        # TODO test leave on weekend?
