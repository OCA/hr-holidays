# Copyright 2023 CGI (https://www.cgi37.com/)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from parameterized import parameterized

from odoo.tests.common import SavepointCase


class TestHrLeaveCalendarMeeting(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Remote test 1",
                "code": "REM1",
                "request_unit": "half_day",
                "color_name": "blue",
                "allocation_type": "fixed",
                "leave_validation_type": "no_validation",
                "create_calendar_meeting": True,
                "calendar_meeting_leave_template": (
                    "%(employee_name)s on %(leave_type_code)s: %(formatted_duration)s"
                ),
            }
        )

        cls.test_user_id = cls.env["res.users"].create(
            {"name": "Test User", "login": "test_user", "email": "mymail@test.com"}
        )
        cls.test_employee_id = cls.env["hr.employee"].create(
            {"name": "Test Employee", "user_id": cls.test_user_id.id}
        )

        cls.leave_allocation1 = cls.env["hr.leave.allocation"].create(
            {
                "name": "Test Allocation Request 1",
                "holiday_status_id": cls.leave_type.id,
                "holiday_type": "employee",
                "employee_id": cls.test_employee_id.id,
                "number_of_days": 10,
            }
        )
        cls.leave_allocation1.action_approve()
        cls.leave_1 = cls.env["hr.leave"].create(
            {
                "name": "Test Leave Request 1",
                "holiday_status_id": cls.leave_type.id,
                "holiday_type": "employee",
                "date_from": "2023-06-15",
                "date_to": "2023-06-17",
                "employee_id": cls.test_employee_id.id,
            }
        )

    @parameterized.expand(
        [
            (
                "",
                "Test Employee on Time Off : 2.00 day(s)",
            ),
            (
                "%(employee_name)s on %(leave_type_code)s: %(formatted_duration)s",
                "Test Employee on REM1: 2.00 day(s)",
            ),
            (
                "%(employee_or_category)s",
                "Test Employee",
            ),
            (
                "%(number_of_hours_display).2f",
                "16.00",
            ),
            (
                "%(number_of_days).2f",
                "2.00",
            ),
            (
                "%(start)s",
                "2023-06-15 00:00:00",
            ),
            (
                "%(stop)s",
                "2023-06-17 00:00:00",
            ),
            (
                "%(leave_type_name)s",
                "Remote test 1",
            ),
            (
                "%(leave_type_code)s",
                "REM1",
            ),
            (
                "%(leave_name)s",
                "Test Leave Request 1",
            ),
        ]
    )
    def test_calendar_meeting_name_from_template(self, template, expected):
        self.leave_type.calendar_meeting_leave_template = template
        self.leave_1.action_validate()
        self.assertEqual(self.leave_1.meeting_id.name, expected)

    def test_calendar_meeting_name_from_template_hour_type(self):
        self.leave_type.request_unit = "hour"
        self.leave_1.action_validate()
        self.assertEqual(
            self.leave_1.meeting_id.name, "Test Employee on REM1: 16.00 hour(s)"
        )
