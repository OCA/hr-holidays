# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests.common import TransactionCase, new_test_user


class TestLeaveTypeVisibility(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Test Sick Leave",
                "company_id": cls.company.id,
                "requires_allocation": False,
                "leave_validation_type": "no_validation",
                "request_unit": "day",
            }
        )
        cls.absent_user = new_test_user(
            cls.env, login="absent_user", groups="base.group_user"
        )
        cls.absent_employee = cls.env["hr.employee"].create(
            {
                "name": "Absent Employee",
                "user_id": cls.absent_user.id,
                "company_id": cls.company.id,
            }
        )
        cls.regular_user = new_test_user(
            cls.env, login="regular_user", groups="base.group_user"
        )
        cls.env["hr.employee"].create(
            {
                "name": "Regular Employee",
                "user_id": cls.regular_user.id,
                "company_id": cls.company.id,
            }
        )
        cls.officer_user = new_test_user(
            cls.env,
            login="officer_user",
            groups="base.group_user,hr_holidays.group_hr_holidays_user",
        )
        cls.leave = (
            cls.env["hr.leave"]
            .with_context(mail_create_nolog=True, mail_notrack=True)
            .create(
                {
                    "name": "Private reason",
                    "employee_id": cls.absent_employee.id,
                    "holiday_status_id": cls.leave_type.id,
                    "request_date_from": date(2026, 3, 2),
                    "request_date_to": date(2026, 3, 2),
                }
            )
        )
        cls.env.flush_all()

    def _report_leave(self, user):
        return (
            self.env["hr.leave.report.calendar"]
            .with_user(user)
            .search([("employee_id", "=", self.absent_employee.id)])
        )

    def test_regular_user_reads_leave_type(self):
        report_leave = self._report_leave(self.regular_user)
        self.assertEqual(len(report_leave), 1)
        self.assertEqual(report_leave.holiday_status_id, self.leave_type)
        self.assertIn(self.leave_type.name, report_leave.name)

    def test_private_description_still_restricted(self):
        report_leave = self._report_leave(self.regular_user)
        self.assertNotIn("description", report_leave.fields_get())
        self.assertIn("description", self._report_leave(self.officer_user).fields_get())
