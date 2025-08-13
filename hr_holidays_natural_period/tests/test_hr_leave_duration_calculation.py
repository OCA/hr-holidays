# Copyright 2020-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from odoo.addons.base.tests.common import SavepointCaseWithUserDemo

from .common import HrLeaveNaturalPeriodTestMixin


@tagged("post_install", "-at_install")
@freeze_time("2023-01-01", tick=True)
class TestHrLeaveDurationCalculation(
    HrLeaveNaturalPeriodTestMixin, SavepointCaseWithUserDemo
):
    """Test leave duration calculation with natural days.

    This test class covers:
    - Basic natural day duration calculation
    - Weekend inclusion logic
    - Working day vs natural day comparison
    - Edge cases with different date ranges
    - Timezone handling in duration calculation

    Test data setup:
    - Uses minimal shared setup in setUpClass
    - Creates test-specific data in setUp method
    - Uses factory methods for consistent test data
    """

    def setUp(self):
        """Set up test-specific data for duration calculation tests."""
        super().setUp()
        self.natural_leave_type = self._create_natural_day_leave_type()
        self.regular_leave_type = self._create_regular_day_leave_type()
        self.employee = self._create_test_employee()

        # Create allocations for both leave types
        self._create_allocation(self.natural_leave_type, self.employee, 20.0)
        self._create_allocation(self.regular_leave_type, self.employee, 20.0)

    def test_weekend_inclusion_friday_to_monday(self):
        """Test weekend inclusion for Friday to Monday leave period.

        Scenario: Employee requests leave from Friday to Monday
        Expected: Natural day calculation should count 4 days (Fri+Sat+Sun+Mon)
        Regular day calculation should count 2 days (Fri+Mon only)

        This test verifies the core functionality of natural day calculation
        by ensuring weekends are properly included in the duration.
        """
        # Given: Leave requests from Friday to Monday
        natural_leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 9, 17, 0),  # Monday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-09"),
        )

        regular_leave = self._create_leave_request(
            self.regular_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 9, 17, 0),  # Monday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-09"),
        )

        # When: Calculating duration
        # Then: Natural day should include weekends, regular should not
        self._assert_duration_equals(
            natural_leave,
            4.0,
            "Natural day leave should count all calendar days including weekends",
        )
        self._assert_duration_equals(
            regular_leave, 2.0, "Regular day leave should count only working days"
        )

    def test_single_day_duration_calculation(self):
        """Test duration calculation for single day leave requests."""
        # Given: Single day leave requests
        natural_leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 6, 17, 0),  # Friday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-06"),
        )

        regular_leave = self._create_leave_request(
            self.regular_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 6, 17, 0),  # Friday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-06"),
        )

        # When/Then: Both should calculate 1 day for single working day
        self._assert_duration_equals(natural_leave, 1.0, "Single day natural leave")
        self._assert_duration_equals(regular_leave, 1.0, "Single day regular leave")

    def test_weekend_only_duration_calculation(self):
        """Test duration calculation for weekend-only leave requests."""
        # Given: Weekend-only leave (Saturday to Sunday)
        natural_leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 7, 9, 0),  # Saturday
            date_to=datetime(2023, 1, 8, 17, 0),  # Sunday
            request_date_from=fields.Date.from_string("2023-01-07"),
            request_date_to=fields.Date.from_string("2023-01-08"),
        )

        regular_leave = self._create_leave_request(
            self.regular_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 7, 9, 0),  # Saturday
            date_to=datetime(2023, 1, 8, 17, 0),  # Sunday
            request_date_from=fields.Date.from_string("2023-01-07"),
            request_date_to=fields.Date.from_string("2023-01-08"),
        )

        # When/Then: Natural day should count weekend, regular should count 0
        self._assert_duration_equals(
            natural_leave, 2.0, "Natural day leave should count weekend days"
        )
        self._assert_duration_equals(
            regular_leave,
            0.0,
            "Regular day leave should not count weekend-only periods",
        )

    def test_full_week_duration_calculation(self):
        """Test duration calculation for full week leave requests."""
        # Given: Full week leave (Monday to Sunday)
        natural_leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 2, 9, 0),  # Monday
            date_to=datetime(2023, 1, 8, 17, 0),  # Sunday
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-08"),
        )

        regular_leave = self._create_leave_request(
            self.regular_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 2, 9, 0),  # Monday
            date_to=datetime(2023, 1, 8, 17, 0),  # Sunday
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-08"),
        )

        # When/Then: Natural day should count all 7 days, regular should count 5
        self._assert_duration_equals(
            natural_leave, 7.0, "Natural day leave should count all 7 days of the week"
        )
        self._assert_duration_equals(
            regular_leave, 5.0, "Regular day leave should count only 5 working days"
        )

    def test_duration_calculation_with_empty_dates(self):
        """Test duration calculation behavior with empty or invalid dates."""
        # Given: Leave request with same start and end date
        leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 2, 9, 0),
            date_to=datetime(2023, 1, 2, 9, 0),  # Same as date_from
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-02"),
        )

        # When: Calculating duration
        duration, _ = leave._get_duration()

        # Then: Should handle edge case gracefully
        self.assertGreaterEqual(
            duration,
            0.0,
            "Duration calculation should handle same start/end dates gracefully",
        )

    def test_timezone_aware_duration_calculation(self):
        """Test that duration calculation properly handles timezone-aware dates."""
        # Given: Leave request with specific timezone considerations
        # Jan 2 is Monday, Jan 3 is Tuesday, Jan 4 is Wednesday (3 weekdays)
        # Using sudo() to ensure proper creation with all required fields
        leave = (
            self.env["hr.leave"]
            .sudo()
            .create(
                {
                    "holiday_status_id": self.natural_leave_type.id,
                    "employee_id": self.employee.id,
                    "date_from": datetime(2023, 1, 2, 23, 0),  # Monday late hour
                    "date_to": datetime(2023, 1, 4, 1, 0),  # Wednesday early hour
                    "request_date_from": fields.Date.from_string("2023-01-02"),
                    "request_date_to": fields.Date.from_string("2023-01-04"),
                }
            )
        )

        # When: Calculating duration
        duration, _ = leave._get_duration()

        # Then: Should properly calculate based on date range, not time
        # For natural days, this should be 3 days (Mon, Tue, Wed)
        self.assertEqual(
            duration,
            3.0,
            "Duration should be calculated based on "
            "date range regardless of specific times",
        )

    def test_duration_calculation_without_resource_calendar(self):
        """Test duration calculation when resource calendar is not available."""
        # Given: Employee without specific resource calendar
        employee_no_calendar = self._create_test_employee(
            name="Employee No Calendar",
            login="no-calendar-employee",
            copy_calendar=False,
        )
        employee_no_calendar.resource_calendar_id = False

        leave = self._create_leave_request(
            self.natural_leave_type,
            employee_no_calendar,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 9, 17, 0),  # Monday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-09"),
        )

        # When: Calculating duration
        duration, _ = leave._get_duration()

        # Then: Should still calculate duration (may use company default calendar)
        self.assertGreater(
            duration,
            0.0,
            "Duration calculation should work even without specific resource calendar",
        )

    def test_cross_month_duration_calculation(self):
        """Test duration calculation across month boundaries."""
        # Given: Leave request spanning across months
        natural_leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 30, 9, 0),  # Monday, end of January
            date_to=datetime(2023, 2, 3, 17, 0),  # Friday, beginning of February
            request_date_from=fields.Date.from_string("2023-01-30"),
            request_date_to=fields.Date.from_string("2023-02-03"),
        )

        # When/Then: Should properly calculate across month boundary
        self._assert_duration_equals(
            natural_leave,
            5.0,
            "Duration calculation should work correctly across month boundaries",
        )
