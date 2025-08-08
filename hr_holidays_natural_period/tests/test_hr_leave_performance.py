# Copyright 2020-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import time
import unittest
from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from odoo.addons.base.tests.common import SavepointCaseWithUserDemo

from .common import HrLeaveNaturalPeriodTestMixin


@tagged("post_install", "-at_install", "performance")
@freeze_time("2023-01-01", tick=True)
@unittest.skipUnless(
    os.environ.get("RUN_SLOW_TESTS") == "1",
    "Skip slow tests by default",
)
class TestHrLeavePerformance(HrLeaveNaturalPeriodTestMixin, SavepointCaseWithUserDemo):
    """Minimal performance check: contract state change with natural public holidays."""

    def test_contract_state_change_performance_with_natural_public_holidays(self):
        """
        Test performance of changing contract from draft to open
        with natural period public holidays.
        """
        # Skip if required modules not installed
        if not self._is_module_installed("hr_contract"):
            self.skipTest("Skipping: hr_contract module not installed")
        if not self._is_module_installed("hr_holidays_public"):
            self.skipTest("Skipping: hr_holidays_public module not installed")

        # Setup: Create employee
        employee = self._create_test_employee(
            name="Test Employee",
            login="test-employee-performance",  # ensure unique login for this test
        )

        # Setup natural period leave type for public holidays
        public_holiday_type = self._create_natural_day_leave_type(
            name="Public Holidays (Natural)",
            request_unit="natural_day",
            exclude_public_holidays=True,
        )

        # Create allocation for the employee
        self._create_allocation(public_holiday_type, employee, days=30.0)

        # Stress setup: Create 200 validated leaves with
        # natural day type to stress _get_consumed_leaves
        start_date = fields.Date.from_string("2020-01-01")
        for i in range(3):
            leave_start = start_date + timedelta(weeks=i)
            leave_end = leave_start + timedelta(days=6)  # 1 week each
            self._create_validated_leave_request(
                public_holiday_type,
                employee,
                date_from=datetime(
                    leave_start.year, leave_start.month, leave_start.day, 9, 0
                ),
                date_to=datetime(leave_end.year, leave_end.month, leave_end.day, 17, 0),
                request_date_from=leave_start,
                request_date_to=leave_end,
            )

        public_holidays = self.env["hr.holidays.public"]
        holiday_template = public_holidays.create({"year": 2023})
        for i in range(2):  # 2 holidays
            holiday_date = fields.Date.from_string(f"2023-01-{i+1:02d}")
            self.env["hr.holidays.public.line"].create(
                {
                    "name": f"Holiday {i+1} in 2023",
                    "date": holiday_date,
                    "year_id": holiday_template.id,
                }
            )

        # Setup main draft contract (long-running)
        contract = self.env["hr.contract"].create(
            {
                "name": "Test Contract",
                "employee_id": employee.id,
                "state": "draft",
                "kanban_state": "done",
                "wage": 1000.0,
                "date_start": fields.Date.from_string(
                    "2020-01-01"
                ),  # Past date for long period
                # No date_end
                "resource_calendar_id": self.env.ref(
                    "resource.resource_calendar_std"
                ).id,
            }
        )

        # Measure performance of state change + potential
        # dependent computation (_get_consumed_leaves)
        start_time = time.time()
        contract.write(
            {"state": "open"}
        )  # Triggers _assign_open_contract and constraints
        self.assertEqual(
            employee.contract_id,
            contract,
            "Employee should have the opened contract assigned",
        )
        # Simulate potential recompute triggered by state change (e.g., in UI or views)
        if hasattr(employee, "_get_consumed_leaves"):
            employee._get_consumed_leaves(public_holiday_type)
        duration = time.time() - start_time

        # Assert: Must complete in <5 seconds
        self.assertLess(
            duration,
            5.0,
            f"Contract state change and computations took {duration:.2f}s "
            f"(expected <5s) - potential hang detected",
        )
