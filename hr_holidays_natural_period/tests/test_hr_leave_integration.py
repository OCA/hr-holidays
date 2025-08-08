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
class TestHrLeaveIntegration(HrLeaveNaturalPeriodTestMixin, SavepointCaseWithUserDemo):
    """Test integration with hr_holidays_public and other modules.

    This test class covers:
    - Integration with hr_holidays_public module
    - Employee consumed leaves calculation
    - Resource calendar integration
    - Context handling in complex scenarios

    Test data setup:
    - Uses minimal shared setup in setUpClass
    - Creates test-specific data in setUp method
    - Conditionally skips tests based on module availability
    """

    def setUp(self):
        """Set up test-specific data for integration tests."""
        super().setUp()
        self.natural_leave_type = self._create_natural_day_leave_type()
        self.regular_leave_type = self._create_regular_day_leave_type()
        self.employee = self._create_test_employee()

    def test_leave_type_exclude_public_holidays_field_availability(self):
        """
        Test that exclude_public_holidays field is available
        when hr_holidays_public is installed.
        """
        if not self._is_module_installed("hr_holidays_public"):
            self.skipTest("hr_holidays_public module not available")

        # Given: A natural day leave type
        leave_type = self.natural_leave_type

        # When: Checking for exclude_public_holidays field
        has_field = hasattr(leave_type, "exclude_public_holidays")

        # Then: Field should be available
        self.assertTrue(
            has_field,
            "exclude_public_holidays field should be "
            "available when hr_holidays_public is installed",
        )

    def test_natural_day_with_public_holidays_integration(self):
        """Test natural day calculation with and without public holidays."""
        if not self._is_module_installed("hr_holidays_public"):
            self.skipTest("hr_holidays_public module not available")

        # Given: A natural day leave type and a week with a public holiday
        leave_type = self.natural_leave_type
        leave_no_excl = self._create_leave_request(
            leave_type,
            self.employee,
            date_from=datetime(2023, 1, 2, 9, 0),
            date_to=datetime(2023, 1, 6, 17, 0),
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-06"),
        )

        if hasattr(leave_type, "exclude_public_holidays"):
            leave_type.exclude_public_holidays = True
        leave_excl = self._create_leave_request(
            leave_type,
            self.employee,
            date_from=datetime(2023, 1, 2, 9, 0),
            date_to=datetime(2023, 1, 6, 17, 0),
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-06"),
        )

        # When
        dur_no_excl, _ = leave_no_excl._get_duration()
        dur_excl, _ = leave_excl._get_duration()

        # Then: Excluding holidays should not increase duration; usually <=
        self.assertGreater(dur_no_excl, 0.0)
        self.assertGreaterEqual(dur_no_excl, dur_excl)

    def test_employee_consumed_leaves_context_handling(self):
        """Test the fixed _get_consumed_leaves method with context handling."""
        # Given: Allocation and leave for natural day leave type
        # Use sudo() to access the employee and leave type with proper permissions
        employee = self.employee.sudo()
        leave_type = self.natural_leave_type.sudo()

        self._create_allocation(leave_type, employee, 10.0)

        # Create leave with sudo() to avoid permission issues
        self._create_validated_leave_request(
            leave_type,
            employee,
            date_from=datetime(2023, 1, 2, 9, 0),
            date_to=datetime(2023, 1, 4, 17, 0),
            request_date_from=fields.Date.from_string("2023-01-02"),
            request_date_to=fields.Date.from_string("2023-01-04"),
        )

        # When: Calculating consumed leaves
        consumed = employee._get_consumed_leaves(leave_type)

        # Then: Should return proper tuple structure
        self.assertIsInstance(
            consumed,
            tuple,
            "_get_consumed_leaves should return a "
            "tuple (consumed_dict, remaining_dict)",
        )
        self.assertEqual(
            len(consumed), 2, "_get_consumed_leaves should return tuple with 2 elements"
        )

        consumed_dict, remaining_dict = consumed
        self.assertTrue(
            consumed_dict or remaining_dict, "At least one dictionary should have data"
        )

    def test_resource_calendar_integration_with_natural_period_context(self):
        """Test resource calendar integration with natural_period context."""
        # Given: Employee with custom calendar
        # Use sudo() for calendar operations to avoid permission issues
        custom_calendar = self.calendar.sudo().copy(
            {"name": "Custom Test Calendar", "tz": "Europe/Madrid"}
        )
        employee = self._create_test_employee(
            name="Calendar Test Employee",
            login="calendar-test-employee",
            calendar=custom_calendar,
            copy_calendar=False,
        )

        leave = self._create_leave_request(
            self.natural_leave_type,
            employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 9, 17, 0),  # Monday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-09"),
        )

        # When: Calculating duration with explicit resource calendar
        resource_calendar = employee.resource_calendar_id
        duration, _ = leave._get_duration(resource_calendar=resource_calendar)

        # Then: Should properly integrate with custom calendar
        self.assertEqual(
            duration,
            4.0,
            "Natural day calculation should work with custom resource calendars",
        )

    def test_process_working_intervals_method_integration(self):
        """Test the _process_working_intervals method integration."""
        # Given: A natural day leave request
        leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 6, 9, 0),  # Friday
            date_to=datetime(2023, 1, 9, 17, 0),  # Monday
            request_date_from=fields.Date.from_string("2023-01-06"),
            request_date_to=fields.Date.from_string("2023-01-09"),
        )

        # When: Processing working intervals
        # (this is called internally by _get_duration)
        duration, _ = leave._get_duration()

        # Then: Should properly process intervals to count unique dates
        self.assertEqual(
            duration,
            4.0,
            "_process_working_intervals should count unique dates correctly",
        )

    def test_timezone_edge_cases_integration(self):
        """Test timezone handling edge cases and DST boundaries."""
        # Given: Calendars with different timezones
        # Use sudo() for calendar operations to avoid permission issues
        utc_calendar = self.calendar.sudo().copy({"name": "UTC Calendar", "tz": "UTC"})
        est_calendar = self.calendar.sudo().copy(
            {"name": "EST Calendar", "tz": "US/Eastern"}
        )

        utc_employee = self._create_test_employee(
            name="UTC Employee",
            login="utc-employee",
            calendar=utc_calendar,
            copy_calendar=False,
        )

        est_employee = self._create_test_employee(
            name="EST Employee",
            login="est-employee",
            calendar=est_calendar,
            copy_calendar=False,
        )

        # When: Creating similar leave requests for both employees
        # Use sudo().create() instead of new() for proper persistence
        utc_leave = (
            self.env["hr.leave"]
            .sudo()
            .create(
                {
                    "holiday_status_id": self.natural_leave_type.id,
                    "employee_id": utc_employee.id,
                    "date_from": datetime(2023, 1, 2, 23, 0),  # Late hour
                    "date_to": datetime(2023, 1, 4, 1, 0),  # Early hour
                    "request_date_from": fields.Date.from_string("2023-01-02"),
                    "request_date_to": fields.Date.from_string("2023-01-04"),
                }
            )
        )

        est_leave = (
            self.env["hr.leave"]
            .sudo()
            .create(
                {
                    "holiday_status_id": self.natural_leave_type.id,
                    "employee_id": est_employee.id,
                    "date_from": datetime(2023, 1, 2, 23, 0),  # Late hour
                    "date_to": datetime(2023, 1, 4, 1, 0),  # Early hour
                    "request_date_from": fields.Date.from_string("2023-01-02"),
                    "request_date_to": fields.Date.from_string("2023-01-04"),
                }
            )
        )

        # Then: Both should calculate the same duration despite timezone differences
        utc_duration, _ = utc_leave._get_duration()
        est_duration, _ = est_leave._get_duration()

        self.assertEqual(
            utc_duration,
            est_duration,
            "Duration calculation should be consistent across different timezones",
        )

        # DST edge: span US/Eastern DST start (2023-03-12)
        est_employee.resource_calendar_id = est_calendar
        dst_leave = (
            self.env["hr.leave"]
            .sudo()
            .create(
                {
                    "holiday_status_id": self.natural_leave_type.id,
                    "employee_id": est_employee.id,
                    "date_from": datetime(2023, 3, 10, 9, 0),
                    "date_to": datetime(2023, 3, 14, 17, 0),
                    "request_date_from": fields.Date.from_string("2023-03-10"),
                    "request_date_to": fields.Date.from_string("2023-03-14"),
                }
            )
        )
        dst_duration, _ = dst_leave._get_duration()
        self.assertEqual(dst_duration, 5.0, "DST change should not affect day count")

    def test_error_handling_edge_cases_integration(self):
        """Test error handling in edge cases during integration scenarios."""
        # Given: Leave request with potential edge case data
        leave = self._create_leave_request(
            self.natural_leave_type,
            self.employee,
            date_from=datetime(2023, 1, 1, 0, 0),  # Start of year
            date_to=datetime(2023, 1, 1, 23, 59),  # End of same day
            request_date_from=fields.Date.from_string("2023-01-01"),
            request_date_to=fields.Date.from_string("2023-01-01"),
        )

        # When: Calculating duration (should not raise exceptions)
        try:
            duration, _ = leave._get_duration()
            calculation_succeeded = True
        except Exception:
            calculation_succeeded = False

        # Then: Should handle edge cases gracefully
        self.assertTrue(
            calculation_succeeded,
            "Duration calculation should handle edge cases without raising exceptions",
        )
