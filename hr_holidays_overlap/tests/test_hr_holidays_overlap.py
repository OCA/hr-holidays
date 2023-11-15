# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrHolidaysOverlap(TransactionCase):
    def setUp(self):
        super().setUp()
        # add our leave after the existing demo sick leave to avoid
        # unintended overlaps
        demo_sick_leave = self.env.ref("hr_holidays.hr_holidays_cl_qdp")
        self.paid_leave = demo_sick_leave.copy(
            default={
                "name": "Paid leave",
                "state": "confirm",
                "holiday_status_id": self.env.ref("hr_holidays.holiday_status_cl").id,
                # those two are needed to circumvent hr.leave#copy_data's check
                "date_from": demo_sick_leave.date_to,
                "date_to": demo_sick_leave.date_to + timedelta(days=2),
            }
        )
        self.paid_leave.action_approve()
        self.paid_leave.action_validate()

    def test_overlap(self):
        """Test that sick leaves may overlap paid leaves and deducts amounts"""
        sick_leave = self.paid_leave.copy(
            default={
                "name": "Sick leave",
                "state": "confirm",
                "holiday_status_id": self.env.ref("hr_holidays.holiday_status_sl").id,
                "date_from": self.paid_leave.date_from,
                "date_to": self.paid_leave.date_from + timedelta(days=1),
            }
        )
        sick_leave.action_validate()
        paid_leave = self.paid_leave.with_context(
            employee_id=self.paid_leave.employee_id.id
        )
        # allocation is 20, with 2 days of paid leave it was 18, adding the sick day makes it 19
        self.assertEqual(
            paid_leave.holiday_status_id.remaining_leaves,
            19,
        )

    def test_no_overlap(self):
        """Test that we still don't allow overlapping for types not configured accordingly"""
        with self.assertRaisesRegex(
            ValidationError, "You can not set 2 time off that overlaps"
        ):
            self.paid_leave.copy(
                default={
                    "state": "confirm",
                    "holiday_status_id": self.env.ref(
                        "hr_holidays.holiday_status_unpaid"
                    ).id,
                    "date_from": self.paid_leave.date_from,
                    "date_to": self.paid_leave.date_to,
                }
            )
