# Copyright 2020-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.base.tests.common import SavepointCaseWithUserDemo

from .common import HrLeaveNaturalPeriodTestMixin


@tagged("post_install", "-at_install")
@freeze_time("2023-01-01", tick=True)
class TestHrLeaveNaturalDayDetection(
    HrLeaveNaturalPeriodTestMixin, SavepointCaseWithUserDemo
):
    """Unit tests for natural day leave type detection logic.

    This test class covers:
    - Detection via request_unit field
    - Detection via context mod_holidays_status_ids
    - Context-based leave type identification
    - Edge cases in detection logic

    Test data setup:
    - Uses minimal shared setup in setUpClass
    - Creates test-specific data in setUp method
    - Uses factory methods for consistent test data
    """

    def setUp(self):
        """Set up test-specific data."""
        super().setUp()
        self.natural_leave_type = self._create_natural_day_leave_type()
        self.regular_leave_type = self._create_regular_day_leave_type()
        self.employee = self._create_test_employee()

    def test_natural_day_detection_with_request_unit_field(self):
        """Test that leave types with request_unit='natural_day' are detected."""
        # Given: A leave request with natural_day leave type
        leave = self._create_leave_request(self.natural_leave_type, self.employee)

        # When: Checking if it's a natural day leave type
        is_natural_day = leave._is_natural_day_leave_type()

        # Then: It should be detected as natural day
        self.assertTrue(
            is_natural_day,
            f"Leave type {self.natural_leave_type.name} with "
            f"request_unit='natural_day' should be detected as natural day",
        )

    def test_regular_day_detection_with_request_unit_field(self):
        """
        Test that leave types with request_unit='day' are not detected as natural day.
        """
        # Given: A leave request with regular day leave type
        leave = self._create_leave_request(self.regular_leave_type, self.employee)

        # When: Checking if it's a natural day leave type
        is_natural_day = leave._is_natural_day_leave_type()

        # Then: It should NOT be detected as natural day
        self.assertFalse(
            is_natural_day,
            f"Leave type {self.regular_leave_type.name} with request_unit='day' "
            "should NOT be detected as natural day",
        )

    def test_natural_day_detection_via_context_mod_holidays_status_ids(self):
        """
        Test that leave types are detected via context mod_holidays_status_ids.
        """
        # Given: A regular leave type that should be treated as natural day via context
        leave = self._create_leave_request(self.regular_leave_type, self.employee)

        # When: Adding the leave type ID to mod_holidays_status_ids context
        leave_with_context = leave.with_context(
            mod_holidays_status_ids=[self.regular_leave_type.id]
        )
        is_natural_day = leave_with_context._is_natural_day_leave_type()

        # Then: It should be detected as natural day due to context
        self.assertTrue(
            is_natural_day,
            f"Leave type {self.regular_leave_type.name} "
            f"should be detected as natural day "
            "when its ID is in context mod_holidays_status_ids",
        )

    def test_context_isolation_does_not_affect_original_leave(self):
        """Test that context changes don't affect the original leave object."""
        # Given: A regular leave type
        leave = self._create_leave_request(self.regular_leave_type, self.employee)

        # When: Creating a context-modified version
        leave_with_context = leave.with_context(
            mod_holidays_status_ids=[self.regular_leave_type.id]
        )

        # Then: Original leave should remain unaffected
        self.assertFalse(
            leave._is_natural_day_leave_type(),
            "Original leave object should not be affected by context changes",
        )
        self.assertTrue(
            leave_with_context._is_natural_day_leave_type(),
            "Context-modified leave should be detected as natural day",
        )

    def test_empty_context_mod_holidays_status_ids(self):
        """Test behavior with empty mod_holidays_status_ids in context."""
        # Given: A regular leave type with empty mod_holidays_status_ids
        leave = self._create_leave_request(self.regular_leave_type, self.employee)
        leave_with_empty_context = leave.with_context(mod_holidays_status_ids=[])

        # When: Checking natural day detection
        is_natural_day = leave_with_empty_context._is_natural_day_leave_type()

        # Then: Should fall back to request_unit field
        self.assertFalse(
            is_natural_day,
            "Leave with empty mod_holidays_status_ids should "
            "fall back to request_unit field",
        )

    def test_multiple_leave_types_in_context(self):
        """Test detection with multiple leave type IDs in context."""
        # Given: Multiple leave types and a context with multiple IDs
        another_leave_type = self._create_regular_day_leave_type(
            name="Another Leave Type"
        )
        leave = self._create_leave_request(self.regular_leave_type, self.employee)

        # When: Adding multiple IDs to context, including our leave type
        leave_with_context = leave.with_context(
            mod_holidays_status_ids=[another_leave_type.id, self.regular_leave_type.id]
        )
        is_natural_day = leave_with_context._is_natural_day_leave_type()

        # Then: Should be detected as natural day
        self.assertTrue(
            is_natural_day,
            "Leave should be detected as natural day when its ID "
            "is among multiple IDs in context",
        )

    def test_context_does_not_override_natural_day_request_unit(self):
        """Test that context doesn't override natural_day request_unit detection."""
        # Given: A natural day leave type
        leave = self._create_leave_request(self.natural_leave_type, self.employee)

        # When: Using context that doesn't include this leave type
        leave_with_context = leave.with_context(mod_holidays_status_ids=[])
        is_natural_day = leave_with_context._is_natural_day_leave_type()

        # Then: Should still be detected as natural day due to request_unit
        self.assertTrue(
            is_natural_day,
            "Natural day leave type should be detected regardless of context",
        )

    def test_detection_without_user_context(self):
        """Test natural day detection works without specific user context."""
        # Given: Leave requests without @users decorator
        natural_leave = self._create_leave_request(
            self.natural_leave_type, self.employee
        )
        regular_leave = self._create_leave_request(
            self.regular_leave_type, self.employee
        )

        # When: Checking detection
        natural_is_detected = natural_leave._is_natural_day_leave_type()
        regular_is_detected = regular_leave._is_natural_day_leave_type()

        # Then: Detection should work correctly
        self.assertTrue(natural_is_detected, "Natural day leave should be detected")
        self.assertFalse(
            regular_is_detected, "Regular day leave should not be detected"
        )
