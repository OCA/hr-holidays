# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestHrLeaveSummaryEmail(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.HrLeave = self.env["hr.leave"]
        leave_type = self.env.ref("hr_holidays.hr_holiday_status_dv")
        # Add allocation days for the test
        leave_type.write({"allocation_type": "no"})
        calendar = self.env.ref("resource.resource_calendar_std")
        partner = self.env["res.partner"].create(
            {
                "name": "Test employee",
                "type": "private",
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test employee",
                "address_home_id": partner.id,
                "resource_calendar_id": calendar.id,
            }
        )
        # Today leave
        self.leave_1 = (
            self.env["hr.leave"]
            .with_context(leave_skip_state_check=True)
            .create(
                {
                    "name": "Test 1",
                    "employee_id": self.employee.id,
                    "holiday_status_id": leave_type.id,
                    "date_from": datetime.today(),
                    "date_to": (datetime.today() + relativedelta(days=1)),
                    "number_of_days": 1,
                    "state": "validate",
                }
            )
        )

        # Week leave
        self.leave_2 = (
            self.env["hr.leave"]
            .with_context(leave_skip_state_check=True)
            .create(
                {
                    "name": "Test 2",
                    "employee_id": self.employee.id,
                    "holiday_status_id": leave_type.id,
                    "date_from": (datetime.today() + relativedelta(days=3)),
                    "date_to": (datetime.today() + relativedelta(days=5)),
                    "number_of_days": 2,
                    "state": "validate",
                }
            )
        )

    def test_hr_leave_summary_no(self):
        """
        No email sent with the default setting in the employee
        """
        self.HrLeave._cron_send_hr_leave_summary_emails()
        self.assertFalse(self.employee.last_hr_leave_summary_sent)

    def test_hr_leave_summary_daily(self):
        """
        Today's active leave is part of the daily email, but the other not.
        """
        domain = self.HrLeave._get_hr_leave_summary_daily_domain(self.env.company.id)
        today_time_offs = self.HrLeave.search(domain)
        self.assertIn(self.leave_1, today_time_offs)
        self.assertNotIn(self.leave_2, today_time_offs)
        self.employee.write({"hr_leave_summary_type": "daily"})
        self.HrLeave._cron_send_hr_leave_summary_emails()
        self.assertEqual(self.employee.last_hr_leave_summary_sent, date.today())

    def test_hr_leave_summary_weekly(self):
        """
        Today's active leave is part of the daily email, as well as the other
        in the same week.
        """
        domain = self.HrLeave._get_hr_leave_summary_weekly_domain(self.env.company.id)
        today_time_offs = self.HrLeave.search(domain)
        self.assertIn(self.leave_1, today_time_offs)
        self.assertIn(self.leave_2, today_time_offs)
        self.employee.write(
            {"hr_leave_summary_type": "weekly", "last_hr_leave_summary_sent": False}
        )
        self.env.company.write(
            {"hr_holidays_summary_weekly_dow": str(date.today().weekday())}
        )
        self.HrLeave._cron_send_hr_leave_summary_emails()
        self.assertEqual(self.employee.last_hr_leave_summary_sent, date.today())
