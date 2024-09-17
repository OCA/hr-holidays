from odoo.tests.common import TransactionCase


class TestHrLeave(TransactionCase):
    def setUp(self):
        super().setUp()
        self.hr_leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Test Leave Type",
                "leave_validation_type": "manager",
                "requires_allocation": "no",
                "request_unit": "hour",
                "time_type": "leave",
            }
        )

        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )

        self.HrLeave = self.env["hr.leave"]

    def test_compute_custom_hours(self):
        hr_leave = self.HrLeave.create(
            {
                "holiday_type": "employee",
                "employee_id": self.employee.id,
                "holiday_status_id": self.hr_leave_type.id,
                "request_unit_hours": True,
                "request_date_from": "2024-07-01",
                "request_time_hour_from": 10.0,
                "request_time_hour_to": 10.5,
            }
        )

        hr_leave._compute_date_from_to()

        self.assertEqual(hr_leave.number_of_hours_display, 0.5)
