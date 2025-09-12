# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo.tests.common import tagged

from odoo.addons.hr_holidays.tests.test_accrual_allocations import (
    TestAccrualAllocations,
)


@tagged("negative_time_off")
class TestHrHolidaysCreditAccrualAllocations(TestAccrualAllocations):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_accrual_leaves_cancel_cron_02(self):
        leave_type_no_negative = self.env["hr.leave.type"].create(
            {
                "name": "Test Accrual - No negative",
                "time_type": "leave",
                "requires_allocation": "yes",
                "allocation_validation_type": "no_validation",
                "leave_validation_type": "no_validation",
                "allows_negative": False,
            }
        )
        leave_type_negative = self.env["hr.leave.type"].create(
            {
                "name": "Test Accrual - Negative",
                "time_type": "leave",
                "requires_allocation": "yes",
                "allocation_validation_type": "no_validation",
                "leave_validation_type": "no_validation",
                "allows_negative": True,
                "max_allowed_negative": 1,
            }
        )
        accrual_plan = (
            self.env["hr.leave.accrual.plan"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "name": "Monthly accrual",
                    "carryover_date": "year_start",
                    "accrued_gain_time": "end",
                    "level_ids": [
                        (
                            0,
                            0,
                            {
                                "added_value_type": "day",
                                "start_count": 0,
                                "start_type": "day",
                                "added_value": 1,
                                "frequency": "monthly",
                                "first_day_display": "last",
                                "cap_accrued_time": False,
                                "action_with_unused_accruals": "maximum",
                                "postpone_max_days": 5,
                            },
                        )
                    ],
                }
            )
        )
        with freeze_time("2024-01-01"):
            self.env["hr.leave.allocation"].create(
                [
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_no_negative.id,
                        "allocation_type": "accrual",
                        "accrual_plan_id": accrual_plan.id,
                        "number_of_days": 1,
                    },
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_negative.id,
                        "allocation_type": "accrual",
                        "accrual_plan_id": accrual_plan.id,
                        "number_of_days": 1,
                    },
                ]
            )
            excess_leave = self.env["hr.leave"].create(
                [
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_no_negative.id,
                        "request_date_from": "2024-01-05",
                        "request_date_to": "2024-01-05",
                    }
                ]
            )
            allowed_negative_leave = self.env["hr.leave"].create(
                [
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_negative.id,
                        "request_date_from": "2024-01-12",
                        "request_date_to": "2024-01-12",
                    }
                ]
            )
            # As accrual allocation don't take into account future leaves,
            # it should be possible to take both leaves.
            self.env["hr.leave"].create(
                [
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_no_negative.id,
                        "request_date_from": "2024-01-04",
                        "request_date_to": "2024-01-04",
                    },
                    {
                        "employee_id": self.employee_emp.id,
                        "holiday_status_id": leave_type_negative.id,
                        "request_date_from": "2024-01-11",
                        "request_date_to": "2024-01-11",
                    },
                ]
            )
            self.env.flush_all()
            # We make the employee not allowed to take negative time off
            leave_type_negative.creditable_employee_ids = [
                (4, self.employee_hrmanager_id)
            ]
            self.env["hr.leave"]._cancel_invalid_leaves()
            # Since both leave are outside an allocation validity, they are
            # detected as discrepancies.
            # And since one of them is in negative excess, and the employee
            # is not allowed to take negative time off, it should be cancelled too.
            self.assertEqual(excess_leave.state, "cancel")
            self.assertEqual(allowed_negative_leave.state, "cancel")
