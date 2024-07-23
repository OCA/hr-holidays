# Copyright 2020-2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form, new_test_user
from odoo.tests.common import users

from odoo.addons.base.tests.common import BaseCommon


@freeze_time("2023-01-01", tick=True)
class TestHrLeave(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = cls.env.ref(
            "hr_holidays_natural_period.hr_leave_type_natural_day_test"
        )
        cls.leave_type_day = cls.env.ref("hr_holidays.holiday_status_cl")
        cls.leave_type_day.employee_requests = "yes"
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
                default_date_to="%s-12-31" % (fields.Date.today().year),
            )
        )

        leave_allocation_form.holiday_status_id = leave_type
        leave_allocation_form.number_of_days_display = days
        return leave_allocation_form.save()

    def _create_hr_leave(self, leave_type, date_from, date_to):
        leave_form = Form(self.env["hr.leave"])
        leave_form.holiday_status_id = leave_type
        leave_form.request_date_from = date_from
        leave_form.request_date_to = date_to
        return leave_form.save()

    @users("test-user")
    def test_hr_leave_natural_day(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 5)
        leave_allocation.sudo().action_validate()
        res_leave_type = (
            self.env["hr.leave.type"]
            .with_company(self.env.company)
            .get_allocation_data_request()[0][1]
        )
        self.assertEqual(res_leave_type["remaining_leaves"], 5)
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], 5)
        self.assertEqual(res_leave_type["max_leaves"], 5)
        self.assertEqual(res_leave_type["leaves_taken"], 0)
        self.assertEqual(res_leave_type["virtual_leaves_taken"], 0)
        self.assertEqual(res_leave_type["request_unit"], "natural_day")
        leave = self._create_hr_leave(self.leave_type, "2023-01-02", "2023-01-05")
        self.assertEqual(leave.number_of_days, 4.0)
        self.assertEqual(leave.number_of_days_display, 4.0)

    @users("test-user")
    def test_hr_leave_day(self):
        leave_allocation = self._create_leave_allocation(self.leave_type_day, 5)
        leave_allocation.sudo().action_validate()
        res_leave_type = (
            self.env["hr.leave.type"]
            .with_company(self.env.company)
            .get_allocation_data_request()[0][1]
        )
        self.assertEqual(res_leave_type["remaining_leaves"], 5)
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], 5)
        self.assertEqual(res_leave_type["max_leaves"], 5)
        self.assertEqual(res_leave_type["leaves_taken"], 0)
        self.assertEqual(res_leave_type["virtual_leaves_taken"], 0)
        self.assertEqual(res_leave_type["request_unit"], "day")
        leave = self._create_hr_leave(self.leave_type_day, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 5)
        self.assertEqual(leave.number_of_days_display, 5)
