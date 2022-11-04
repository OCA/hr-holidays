# Copyright 2020-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, common


class TestHrLeave(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HrLeave = cls.env["hr.leave"]
        cls.leave_type = cls.env.ref(
            "hr_holidays_natural_period.hr_leave_type_natural_day_test"
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
                "type": "private",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test employee",
                "address_home_id": partner.id,
                "resource_calendar_id": calendar.id,
            }
        )

    def test_hr_leave_natural_day(self):
        leave_form = Form(
            self.HrLeave.with_context(
                default_employee_id=self.employee.id,
            )
        )
        leave_form.holiday_status_id = self.leave_type
        leave_form.request_date_from = "2021-01-02"
        leave_form.request_date_to = "2021-01-05"
        self.assertEqual(leave_form.number_of_days, 4.0)

    def test_hr_leave_day(self):
        leave_form = Form(
            self.HrLeave.with_context(
                default_employee_id=self.employee.id,
            )
        )
        leave_form.holiday_status_id = self.env.ref("hr_holidays.holiday_status_cl")
        leave_form.request_date_from = "2021-01-02"  # Saturday
        leave_form.request_date_to = "2021-01-04"  # Monday
        self.assertEqual(leave_form.number_of_days, 1)
