# Copyright 2026 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests.common import TransactionCase


class TestHolidaysApprovals(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )

        cls.leave_hours = cls.env["hr.leave.type"].create(
            {
                "name": "Hours Approval",
                "leave_validation_type": "hr",
                "validation_type_split": "hours",
                "request_unit": "hour",
                "requires_allocation": "no",
            }
        )

        cls.leave_days = cls.env["hr.leave.type"].create(
            {
                "name": "Days Approval",
                "leave_validation_type": "hr",
                "validation_type_split": "days",
                "request_unit": "hour",
                "requires_allocation": "no",
            }
        )

        cls.leave_no_validation = cls.env["hr.leave.type"].create(
            {
                "name": "No Approval",
                "leave_validation_type": "no_validation",
                "request_unit": "day",
                "requires_allocation": "no",
            }
        )

    def _create_leave(self, leave_type, date_from, date_to, request_hours=False):
        return self.env["hr.leave"].create(
            {
                "employee_id": self.employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": date_from,
                "request_date_to": date_to,
                "request_unit_hours": request_hours,
                "request_unit_half": False,
            }
        )

    def test_hours_request_requires_approval_when_hours_type(self):
        leave = self._create_leave(
            self.leave_hours,
            datetime(2026, 3, 25, 8, 0),
            datetime(2026, 3, 25, 10, 0),
            request_hours=True,
        )
        self.assertEqual(leave.state, "confirm")

    def test_days_request_auto_validated_when_hours_type(self):
        leave = self._create_leave(
            self.leave_hours,
            datetime(2026, 3, 25),
            datetime(2026, 3, 26),
            request_hours=False,
        )
        self.assertEqual(leave.state, "validate")

    def test_days_request_requires_approval_when_days_type(self):
        leave = self._create_leave(
            self.leave_days,
            datetime(2026, 3, 25),
            datetime(2026, 3, 26),
            request_hours=False,
        )
        self.assertEqual(leave.state, "confirm")

    def test_no_validation_type_is_always_validated(self):
        leave = self._create_leave(
            self.leave_no_validation,
            datetime(2026, 3, 25),
            datetime(2026, 3, 26),
            request_hours=False,
        )
        self.assertEqual(leave.state, "validate")
