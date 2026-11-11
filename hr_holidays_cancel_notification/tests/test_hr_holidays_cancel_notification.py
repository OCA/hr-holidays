# Copyright 2026 Creublanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.addons.hr_holidays.tests.common import TestHrHolidaysCommon


class TestHrHolidaysCancelNotification(TestHrHolidaysCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_emp.leave_manager_id = cls.user_hrmanager
        cls.hr_leave_type = (
            cls.env["hr.leave.type"]
            .with_user(cls.user_hrmanager)
            .create(
                {
                    "name": "Leave Type",
                    "requires_allocation": "no",
                }
            )
        )
        cls.leave = (
            cls.env["hr.leave"]
            .with_context(mail_create_nolog=True, mail_notrack=True)
            .with_user(cls.user_employee)
            .create(
                {
                    "name": "Leave 1",
                    "employee_id": cls.employee_emp.id,
                    "holiday_status_id": cls.hr_leave_type.id,
                    "date_from": "2018-02-05 07:00:00",
                    "date_to": "2018-02-08 07:00:00",
                    "number_of_days": 3,
                }
            )
        )
        cls.leave.with_user(cls.user_hrmanager).action_validate()

    @freeze_time("2018-02-05")
    def test_cancel_notifies_responsible(self):
        self.env["hr.holidays.cancel.leave"].with_user(self.user_employee).with_context(
            default_leave_id=self.leave.id
        ).new({"reason": "Personal reasons"}).action_cancel_leave()
        self.assertFalse(self.leave.active, "The canceled leave should be archived.")
        message = self.env["mail.message"].search(
            [
                ("model", "=", "hr.leave"),
                ("res_id", "=", self.leave.id),
                ("body", "like", "Personal reasons"),
            ]
        )
        self.assertTrue(message, "A cancellation message should be posted.")
        self.assertIn(
            self.user_hrmanager.partner_id,
            message.partner_ids,
            "The leave manager should be notified of the cancellation.",
        )

    @freeze_time("2018-02-05")
    def test_cancel_without_responsible(self):
        self.employee_emp.write({"leave_manager_id": False, "parent_id": False})
        self.env["hr.holidays.cancel.leave"].with_user(self.user_employee).with_context(
            default_leave_id=self.leave.id
        ).new({"reason": "Personal reasons"}).action_cancel_leave()
        self.assertFalse(self.leave.active, "The canceled leave should be archived.")
        message = self.env["mail.message"].search(
            [
                ("model", "=", "hr.leave"),
                ("res_id", "=", self.leave.id),
                ("body", "like", "has canceled their time off"),
            ]
        )
        self.assertFalse(
            message, "No notification should be posted without a responsible."
        )
