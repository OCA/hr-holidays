# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests.common import Form

from odoo.addons.hr_holidays.tests.common import TestHrHolidaysCommon


class TestHRLeave(TestHrHolidaysCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.leave_type_hour_unlimited = cls.env["hr.leave.type"].create(
            {
                "name": "Test unlimited leave type",
                "request_unit": "hour",
                "requires_allocation": "no",
            }
        )

    def _create_user_leave(self, user, from_datetime, to_datetime):
        """Request a leave for `user` from `from_datetime` to `to_datetime`."""
        leave_form = Form(self.env["hr.leave"].with_user(user))
        leave_form.name = "Test leave"
        leave_form.holiday_status_id = self.leave_type_hour_unlimited
        leave_form.request_unit_hours = True
        leave_form.request_date_from = from_datetime.date()
        leave_form.custom_hours_request_date_to = to_datetime.date()

        # Module `hr_leave_custom_hour_interval` makes hours fields readonly
        from_hour = from_datetime.hour
        if "request_time_hour_from" in leave_form._view["fields"]:
            leave_form.request_time_hour_from = from_hour
        else:
            leave_form.request_hour_from = str(from_hour)

        to_hour = to_datetime.hour
        if "request_time_hour_to" in leave_form._view["fields"]:
            leave_form.request_time_hour_to = to_hour
        else:
            leave_form.request_hour_to = str(to_hour)
        return leave_form.save()

    def test_custom_hours_date_to(self):
        """Request a leave from 10 AM to 10 AM of following week.
        The leave counts all the working hours in a week.
        """
        # Arrange
        user = self.user_employee
        leave_from = datetime(2019, 5, 6, 10)
        leave_to = leave_from + timedelta(weeks=1)
        working_hours = user.employee_resource_calendar_id
        leave_duration_hours = working_hours.get_work_duration_data(
            leave_from, leave_to
        )["hours"]
        # pre-condition
        self.assertEqual(leave_duration_hours, 40)

        # Act
        leave = self._create_user_leave(user, leave_from, leave_to)

        # Assert
        self.assertEqual(leave.number_of_hours_display, leave_duration_hours)
