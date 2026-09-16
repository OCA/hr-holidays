# Copyright 2020-2025 Tecnativa - Víctor Martínez
# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests import Form, new_test_user
from odoo.tests.common import users
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestHrLeave(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Natural Day Test Leave Type",
                "request_unit": "natural_day",
                "requires_allocation": True,
                "employee_requests": True,
            }
        )
        cls.leave_type_day = cls.env["hr.leave.type"].create(
            {
                "name": "Test Day Leave Type",
                "request_unit": "day",
                "requires_allocation": True,
                "employee_requests": True,
            }
        )

        calendar = cls.env.ref("resource.resource_calendar_std")
        calendar = calendar.copy({"name": "Test calendar"})
        calendar.switch_calendar_type()
        calendar.attendance_ids.filtered(
            lambda x: x.week_type == "0"
            and not x.display_type
            and x.day_period == "afternoon"
        ).unlink()
        calendar.attendance_ids.filtered(
            lambda x: x.week_type == "1"
            and not x.display_type
            and x.day_period == "morning"
        ).unlink()
        partner = cls.env["res.partner"].create(
            {
                "name": "Test employee",
                "type": "other",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.user = new_test_user(cls.env, login="test-user")
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test employee",
                "address_id": partner.id,
                "resource_calendar_id": calendar.id,
                "user_id": cls.user.id,
            }
        )

    def _create_leave_allocation(self, leave_type, days):
        leave_allocation_form = Form(
            self.env["hr.leave.allocation"].with_context(
                default_date_from="2023-01-01",
                default_date_to=f"{fields.Date.today().year}-12-31",
            )
        )
        leave_allocation_form.holiday_status_id = leave_type
        leave_allocation_form.number_of_days_display = days
        return leave_allocation_form.save()

    def _create_hr_leave(self, leave_type, date_from, date_to=None):
        if leave_type.request_unit == "natural_day_half_day":
            return self.env["hr.leave"].create(
                {
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date_from,
                    "request_date_to": date_to or date_from,
                    "request_unit_half": True,
                    "request_date_from_period": "am",
                    "employee_id": self.employee.id,
                }
            )

        leave_form = Form(self.env["hr.leave"])
        leave_form.holiday_status_id = leave_type
        leave_form.request_date_from = date_from
        if date_to:
            leave_form.request_date_to = date_to
        return leave_form.save()

    def _test_hr_leave_natural_day_01(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 5)
        leave_allocation.sudo()._action_validate()

        self.assertEqual(leave_allocation.number_of_days, 5)
        self.assertEqual(
            self.leave_type.request_unit in ("natural_day", "natural_day_half_day"),
            True,
        )

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_01(self):
        self._test_hr_leave_natural_day_01()
        leave = self._create_hr_leave(self.leave_type, "2023-01-02", "2023-01-05")
        self.assertEqual(leave.number_of_days, 4.0)

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_half_day_01(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self._test_hr_leave_natural_day_01()
        leave = self._create_hr_leave(self.leave_type, "2023-01-02")
        self.assertEqual(leave.number_of_days, 0.5)

    def _test_hr_leave_natural_day_02(self):
        attendances = []
        for i in range(0, 5):
            attendances.append((i, "morning", 10, 14))
            attendances.append((i, "afternoon", 16, 20))
        r_sudo = self.env["resource.calendar"].sudo()
        calendar = r_sudo.create(
            {
                "name": "Test calendar",
                "tz": "Europe/Brussels",
                "attendance_ids": [
                    Command.create(
                        {
                            "name": index,
                            "dayofweek": str(att[0]),
                            "day_period": att[1],
                            "hour_from": att[2],
                            "hour_to": att[3],
                        },
                    )
                    for index, att in enumerate(attendances)
                ],
            }
        )
        self.employee.resource_calendar_id = calendar
        leave_allocation = self._create_leave_allocation(self.leave_type, 9)
        leave_allocation.sudo()._action_validate()

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_with_leave_in_middle(self):
        self.env["resource.calendar.leaves"].sudo().create(
            {
                "name": "Leave in middle",
                "calendar_id": self.employee.resource_calendar_id.id,
                "resource_id": self.employee.resource_id.id,
                "date_from": "2023-01-03 08:00:00",
                "date_to": "2023-01-03 16:00:00",
                "time_type": "leave",
            }
        )
        self._test_hr_leave_natural_day_01()
        leave = self._create_hr_leave(self.leave_type, "2023-01-02", "2023-01-05")
        self.assertEqual(leave.number_of_days, 4.0)

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_half_day_with_leave_in_middle(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.env["resource.calendar.leaves"].sudo().create(
            {
                "name": "Leave in middle",
                "calendar_id": self.employee.resource_calendar_id.id,
                "resource_id": self.employee.resource_id.id,
                "date_from": "2023-01-03 08:00:00",
                "date_to": "2023-01-03 16:00:00",
                "time_type": "leave",
            }
        )
        self._test_hr_leave_natural_day_01()
        leave = self._create_hr_leave(self.leave_type, "2023-01-02", "2023-01-05")
        self.assertEqual(leave.number_of_days, 2.0)

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_02(self):
        self._test_hr_leave_natural_day_02()
        leave = self._create_hr_leave(self.leave_type, "2023-01-01", "2023-01-09")
        self.assertEqual(leave.number_of_days, 9.0)

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_natural_day_half_day_02(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self._test_hr_leave_natural_day_02()
        leave = self._create_hr_leave(self.leave_type, "2023-01-01")
        self.assertEqual(leave.number_of_days, 0.5)

    @users("test-user")
    def test_hr_leave_natural_day_no_manager(self):
        """An employee that is not a manager
        can create a natural day leave in the future with no validation.
        """
        leave_type = self.leave_type
        leave_type.requires_allocation = False
        leave_type.leave_validation_type = "no_validation"
        leave = self._create_hr_leave(leave_type, "3000-01-01", "3000-01-01")
        self.assertEqual(leave.state, "validate")

    @users("test-user")
    @mute_logger("odoo.models.unlink")
    def test_hr_leave_day(self):
        leave_allocation = self._create_leave_allocation(self.leave_type_day, 5)
        leave_allocation.sudo()._action_validate()

        self.assertEqual(leave_allocation.number_of_days, 5)
        self.assertEqual(self.leave_type_day.request_unit, "day")
        leave = self._create_hr_leave(self.leave_type_day, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 5)
