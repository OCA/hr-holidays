# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.hr_holidays.tests.common import TestHrHolidaysCommon


class TestExtend(TestHrHolidaysCommon):
    def test_time_type(self):
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Paid Time Off",
                "time_type": "leave",
                "auto_extend": True,
                "allocation_type": "no",
                "validity_start": False,
            }
        )
        date_to = fields.Date.today() - timedelta(days=2)
        f = Form(self.env["hr.leave"])
        f.name = "Doctor Appointment"
        f.employee_id = self.env["hr.employee"].browse(self.employee_hruser_id)
        f.holiday_status_id = leave_type
        f.request_date_from = fields.Date.today() - timedelta(days=5)
        f.request_date_to = date_to
        leave_1 = f.save()
        self.assertEqual(leave_1.request_date_to, date_to)
        self.env["hr.leave"]._cron_auto_extend()
        self.assertEqual(leave_1.request_date_to, date_to)
        leave_1.action_approve()
        self.assertEqual(leave_1.request_date_to, date_to)
        self.assertEqual(
            self.env["resource.calendar.leaves"]
            .search([("holiday_id", "=", leave_1.id)])
            .time_type,
            "leave",
        )
        self.env["hr.leave"]._cron_auto_extend()
        self.assertEqual(leave_1.request_date_to, date_to + timedelta(days=7))

    def test_extend_overlap(self):
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Paid Time Off",
                "time_type": "leave",
                "auto_extend": True,
                "allocation_type": "no",
                "validity_start": False,
            }
        )
        leave_type_02 = self.env["hr.leave.type"].create(
            {
                "name": "Another leave type",
                "time_type": "leave",
                "allocation_type": "no",
                "validity_start": False,
            }
        )
        date_to = fields.Date.today() - timedelta(days=2)
        f = Form(self.env["hr.leave"])
        f.name = "Doctor Appointment"
        f.employee_id = self.env["hr.employee"].browse(self.employee_hruser_id)
        f.holiday_status_id = leave_type
        f.request_date_from = fields.Date.today() - timedelta(days=5)
        f.request_date_to = date_to
        leave_1 = f.save()

        f2 = Form(self.env["hr.leave"])
        f2.name = "Doctor Appointment"
        f2.employee_id = self.env["hr.employee"].browse(self.employee_hruser_id)
        f2.holiday_status_id = leave_type_02
        f2.request_date_from = fields.Date.today() - timedelta(days=1)
        f2.request_date_to = fields.Date.today()
        leave_2 = f2.save()
        self.assertTrue(leave_1.auto_extend)
        self.assertFalse(leave_2.auto_extend)
        leave_1.action_approve()
        leave_2.action_approve()
        self.assertTrue(leave_1.auto_extend)
        self.assertFalse(leave_1.activity_ids)
        self.env["hr.leave"]._cron_auto_extend()
        leave_1.flush()
        leave_1.refresh()
        self.assertFalse(leave_1.auto_extend)
        self.assertTrue(leave_1.activity_ids)
