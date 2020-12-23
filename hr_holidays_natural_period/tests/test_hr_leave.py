# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestHrLeave(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HrLeave = cls.env["hr.leave"]
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Test partner",
                "request_unit": "natural_day",
                "responsible_id": cls.env.ref("base.user_admin").id,
            }
        )
        calendar = cls.env.ref("resource.resource_calendar_std")
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
        leave_request = self.HrLeave.new(
            {
                "date_from": "2021-01-02 00:00:00",
                "date_to": "2021-01-04 23:59:59",
                "holiday_status_id": self.leave_type.id,
                "employee_id": self.employee.id,
            }
        )
        leave_request._onchange_leave_dates()
        self.assertEquals(leave_request.number_of_days, 3.0)

    def test_hr_leave_day(self):
        leave_request = self.HrLeave.new(
            {
                "date_from": "2021-01-02 00:00:00",  # Saturday
                "date_to": "2021-01-05 00:00:00",  # Monday
                "holiday_status_id": self.env.ref("hr_holidays.holiday_status_cl").id,
                "employee_id": self.employee.id,
            }
        )
        leave_request._onchange_leave_dates()
        self.assertEquals(leave_request.number_of_days, 1)
