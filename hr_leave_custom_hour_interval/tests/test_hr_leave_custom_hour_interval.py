from datetime import date

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestHRLeaveRequest(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a new employee to avoid conflicts
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "work_email": "test.employee@example.com",
            }
        )

        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Legal Leaves",
                "time_type": "leave",
                "request_unit": "hour",
                "requires_allocation": "no",
            }
        )
        today = date.today()

        hour_from = 8.0
        hour_to = 14.0

        cls.first_leave = cls.env["hr.leave"].create(
            {
                "name": "Christmas",
                "employee_id": cls.employee.id,
                "request_unit_hours": True,
                "holiday_status_id": cls.leave_type.id,
                "request_time_hour_from": hour_from,
                "request_time_hour_to": hour_to,
                "request_date_from": today,
                "request_date_to": today,
            }
        )

    def test_leave_created_correctly(self):
        self.assertEqual(self.first_leave.name, "Christmas")
        self.assertEqual(self.first_leave.employee_id.id, self.employee.id)
        self.assertEqual(self.first_leave.holiday_status_id.id, self.leave_type.id)
        self.assertEqual(self.first_leave.request_time_hour_from, 8.0)
        self.assertEqual(self.first_leave.request_time_hour_to, 14.0)
        self.assertEqual(self.first_leave.duration_display, "5:00 hours")
