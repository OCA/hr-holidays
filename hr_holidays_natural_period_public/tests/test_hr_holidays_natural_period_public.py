# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import Form, new_test_user
from odoo.tests.common import users

from odoo.addons.base.tests.common import BaseCommon


class TestHrHolidaysNaturalPeriodPublic(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["res.partner"]
        cls.employee_model = cls.env["hr.employee"]
        cls.public_holiday_model = cls.env["hr.holidays.public"]
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
        partner = cls.partner_model.create(
            {
                "name": "Test employee",
                "type": "private",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.user = new_test_user(cls.env, login="test-user")
        cls.employee = cls.employee_model.create(
            {
                "name": "Test employee",
                "address_home_id": partner.id,
                "resource_calendar_id": calendar.id,
                "user_id": cls.user.id,
            }
        )
        cls.public_holiday = cls.public_holiday_model.create(
            {
                "year": 2023,
                "country_id": False,
            }
        )

    def _create_leave_allocation(self, leave_type, days):
        leave_allocation_form = Form(
            self.env["hr.leave.allocation"].with_context(
                default_date_from="2023-01-01",
                default_date_to="%s-12-31" % fields.Date.today().year,
            )
        )
        leave_allocation_form.name = "TEST"
        leave_allocation_form.holiday_status_id = leave_type
        leave_allocation_form.number_of_days_display = days
        return leave_allocation_form.save()

    def _create_hr_leave(self, leave_type, date_from, date_to):
        leave_form = Form(self.env["hr.leave"])
        leave_form.holiday_status_id = leave_type
        leave_form.request_date_from = date_from
        leave_form.request_date_to = date_to
        return leave_form.save()

    def _create_public_holiday_line(self, name, date, year):
        public_holiday_line = Form(self.env["hr.holidays.public.line"].sudo())
        public_holiday_line.name = name
        public_holiday_line.date = date
        public_holiday_line.year_id = year
        return public_holiday_line.save()

    @users("test-user")
    def test_hr_leave_natural_day(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 10)
        leave_allocation.action_confirm()
        leave_allocation.sudo().action_validate()
        res_leave_type = self.env["hr.leave.type"].get_days_all_request()[0][1]
        self.assertEqual(res_leave_type["remaining_leaves"], "10")
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], "10")
        self.assertEqual(res_leave_type["max_leaves"], "10")
        self.assertEqual(res_leave_type["leaves_taken"], "0")
        self.assertEqual(res_leave_type["virtual_leaves_taken"], "0")
        self.assertEqual(res_leave_type["request_unit"], self.leave_type.request_unit)
        leave = self._create_hr_leave(self.leave_type, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 8)
        self.assertEqual(leave.number_of_days_display, 8)

    def test_hr_leave_natural_day_half_day(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.test_hr_leave_natural_day()

    @users("test-user")
    def test_hr_leave_natural_day_public_holiday_01(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 10)
        leave_allocation.action_confirm()
        leave_allocation.sudo().action_validate()
        self._create_public_holiday_line("P1", "2023-01-09", self.public_holiday)
        res_leave_type = self.env["hr.leave.type"].get_days_all_request()[0][1]
        self.assertEqual(res_leave_type["remaining_leaves"], "10")
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], "10")
        self.assertEqual(res_leave_type["max_leaves"], "10")
        self.assertEqual(res_leave_type["leaves_taken"], "0")
        self.assertEqual(res_leave_type["virtual_leaves_taken"], "0")
        self.assertEqual(res_leave_type["request_unit"], self.leave_type.request_unit)
        self.assertEqual(self.leave_type.exclude_public_holidays, False)
        leave = self._create_hr_leave(self.leave_type, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 8)
        self.assertEqual(leave.number_of_days_display, 8)

    @users("test-user")
    def test_hr_leave_natural_day_public_holiday_02(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 10)
        leave_allocation.action_confirm()
        leave_allocation.sudo().action_validate()
        self._create_public_holiday_line("P1", "2023-01-09", self.public_holiday)
        self.leave_type.write({"exclude_public_holidays": True})
        res_leave_type = self.env["hr.leave.type"].get_days_all_request()[0][1]
        self.assertEqual(res_leave_type["remaining_leaves"], "10")
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], "10")
        self.assertEqual(res_leave_type["max_leaves"], "10")
        self.assertEqual(res_leave_type["leaves_taken"], "0")
        self.assertEqual(res_leave_type["virtual_leaves_taken"], "0")
        self.assertEqual(res_leave_type["request_unit"], self.leave_type.request_unit)
        self.assertEqual(self.leave_type.exclude_public_holidays, True)
        leave = self._create_hr_leave(self.leave_type, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 7)
        self.assertEqual(leave.number_of_days_display, 7)

    def test_hr_leave_natural_day_half_day_public_holiday_01(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.test_hr_leave_natural_day_public_holiday_01()

    def test_hr_leave_natural_day_half_day_public_holiday_02(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.test_hr_leave_natural_day_public_holiday_02()

    @users("test-user")
    def test_hr_leave_natural_day_public_holiday_weekend_01(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 10)
        leave_allocation.action_confirm()
        leave_allocation.sudo().action_validate()
        self._create_public_holiday_line("P1", "2023-01-14", self.public_holiday)
        res_leave_type = self.env["hr.leave.type"].get_days_all_request()[0][1]
        self.assertEqual(res_leave_type["remaining_leaves"], "10")
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], "10")
        self.assertEqual(res_leave_type["max_leaves"], "10")
        self.assertEqual(res_leave_type["leaves_taken"], "0")
        self.assertEqual(res_leave_type["virtual_leaves_taken"], "0")
        self.assertEqual(res_leave_type["request_unit"], self.leave_type.request_unit)
        self.assertEqual(self.leave_type.exclude_public_holidays, False)
        leave = self._create_hr_leave(self.leave_type, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 8)
        self.assertEqual(leave.number_of_days_display, 8)

    @users("test-user")
    def test_hr_leave_natural_day_public_holiday_weekend_02(self):
        leave_allocation = self._create_leave_allocation(self.leave_type, 10)
        leave_allocation.action_confirm()
        leave_allocation.sudo().action_validate()
        self._create_public_holiday_line("P1", "2023-01-14", self.public_holiday)
        self.leave_type.write({"exclude_public_holidays": True})
        res_leave_type = self.env["hr.leave.type"].get_days_all_request()[0][1]
        self.assertEqual(res_leave_type["remaining_leaves"], "10")
        self.assertEqual(res_leave_type["virtual_remaining_leaves"], "10")
        self.assertEqual(res_leave_type["max_leaves"], "10")
        self.assertEqual(res_leave_type["leaves_taken"], "0")
        self.assertEqual(res_leave_type["virtual_leaves_taken"], "0")
        self.assertEqual(res_leave_type["request_unit"], self.leave_type.request_unit)
        self.assertEqual(self.leave_type.exclude_public_holidays, True)
        leave = self._create_hr_leave(self.leave_type, "2023-01-08", "2023-01-15")
        self.assertEqual(leave.number_of_days, 7)
        self.assertEqual(leave.number_of_days_display, 7)

    def test_hr_leave_natural_day_half_day_public_holiday_weekend_01(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.test_hr_leave_natural_day_public_holiday_weekend_01()

    def test_hr_leave_natural_day_half_day_public_holiday_weekend_02(self):
        self.leave_type.request_unit = "natural_day_half_day"
        self.test_hr_leave_natural_day_public_holiday_weekend_02()
