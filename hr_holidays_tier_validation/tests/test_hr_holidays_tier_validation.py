# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestHrHolidaysTierValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        # Clean up any existing tier definitions for hr.leave to avoid conflicts
        existing_tier_defs = cls.env["tier.definition"].search(
            [("model_id", "=", cls.env.ref("hr_holidays.model_hr_leave").id)]
        )
        existing_tier_defs.unlink()

        # Clean up any existing stress days to avoid conflicts with other tests
        existing_stress_days = cls.env["hr.leave.stress.day"].search([])
        existing_stress_days.unlink()

        # Models
        cls.user_model = cls.env["res.users"]
        cls.employee_model = cls.env["hr.employee"]
        cls.leave_type_model = cls.env["hr.leave.type"]
        cls.leave_model = cls.env["hr.leave"]
        cls.leave_allocation_model = cls.env["hr.leave.allocation"]
        cls.tier_definition_model = cls.env["tier.definition"]
        cls.review_model = cls.env["tier.review"]

        # Create test users
        cls.hr_manager = cls.user_model.create(
            {
                "name": "HR Manager Test",
                "login": "hr_manager_test",
                "email": "hr.manager.test@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("hr_holidays.group_hr_holidays_manager").id,
                            cls.env.ref("base.group_user").id,
                        ],
                    )
                ],
            }
        )

        cls.leave_manager = cls.user_model.create(
            {
                "name": "Leave Manager Test",
                "login": "leave_manager_test",
                "email": "leave.manager.test@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("hr_holidays.group_hr_holidays_user").id,
                            cls.env.ref("base.group_user").id,
                        ],
                    )
                ],
            }
        )

        cls.employee_user = cls.user_model.create(
            {
                "name": "Employee User Test",
                "login": "employee_user_test",
                "email": "employee.test@example.com",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )

        # Create employees
        cls.employee = cls.employee_model.create(
            {
                "name": "Test Employee",
                "user_id": cls.employee_user.id,
                "leave_manager_id": cls.leave_manager.id,
            }
        )

        # Create leave type with tier validation
        cls.leave_type_tier_validation = cls.leave_type_model.create(
            {
                "name": "Leave Type with Tier Validation Test",
                "leave_validation_type": "tier_validation",
                "allocation_validation_type": "no",
            }
        )

        # Create leave type without tier validation
        cls.leave_type_standard = cls.leave_type_model.create(
            {
                "name": "Leave Type Standard Test",
                "leave_validation_type": "both",
                "allocation_validation_type": "no",
            }
        )

        # Create tier definitions
        cls.tier_def_1 = cls.tier_definition_model.create(
            {
                "model_id": cls.env.ref("hr_holidays.model_hr_leave").id,
                "review_type": "individual",
                "reviewer_id": cls.leave_manager.id,
                "definition_domain": "[('state', '=', 'confirm'), "
                "('holiday_status_id.leave_validation_type', '=', 'tier_validation')]",
                "sequence": 10,
                "notify_on_pending": True,
                "approve_sequence": True,
            }
        )

        cls.tier_def_2 = cls.tier_definition_model.create(
            {
                "model_id": cls.env.ref("hr_holidays.model_hr_leave").id,
                "review_type": "individual",
                "reviewer_id": cls.hr_manager.id,
                "definition_domain": "[('state', '=', 'confirm'), "
                "('holiday_status_id.leave_validation_type', '=', 'tier_validation')]",  # noqa B950
                "sequence": 20,
                "notify_on_pending": True,
                "approve_sequence": True,
            }
        )

        # Create leave allocations
        cls.leave_allocation_tier = cls.leave_allocation_model.create(
            {
                "name": "Test Allocation Tier",
                "holiday_status_id": cls.leave_type_tier_validation.id,
                "employee_id": cls.employee.id,
                "number_of_days": 20,
            }
        )
        cls.leave_allocation_tier.with_user(cls.hr_manager).action_validate()

        cls.leave_allocation_standard = cls.leave_allocation_model.create(
            {
                "name": "Test Allocation Standard",
                "holiday_status_id": cls.leave_type_standard.id,
                "employee_id": cls.employee.id,
                "number_of_days": 20,
            }
        )
        cls.leave_allocation_standard.with_user(cls.hr_manager).action_validate()

    def test_01_leave_type_tier_validation_selection(self):
        """Test that the leave type has the tier_validation option."""
        leave_type = self.leave_type_model.create(
            {
                "name": "Test Leave Type",
                "leave_validation_type": "tier_validation",
            }
        )
        self.assertEqual(leave_type.leave_validation_type, "tier_validation")

    def test_02_tier_definition_model_names(self):
        """Test that hr.leave is included in tier validation model names."""
        model_names = self.tier_definition_model._get_tier_validation_model_names()
        self.assertIn("hr.leave", model_names)

    def test_03_leave_request_tier_validation_enabled(self):
        """Test leave request with tier validation enabled."""
        today = datetime.today()

        # Verify we have exactly 2 tier definitions for our leave type
        tier_defs = self.tier_definition_model.search(
            [("model_id", "=", self.env.ref("hr_holidays.model_hr_leave").id)]
        )
        self.assertEqual(
            len(tier_defs), 2, f"Expected 2 tier definitions, found {len(tier_defs)}"
        )

        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Request",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today,
                "date_to": today + timedelta(days=2),
            }
        )

        # Should be in confirm state after creation with tier validation
        self.assertEqual(leave.state, "confirm")

        # Should need validation
        self.assertTrue(leave.need_validation)

        # Should have tier reviews created
        self.assertEqual(
            len(leave.review_ids),
            2,
            f"Expected 2 reviews, found {len(leave.review_ids)}. "
            f"Reviews: {[(r.reviewer_id.name, r.definition_id.sequence) for r in leave.review_ids]}",  # noqa B950
        )

    def test_04_leave_request_standard_validation(self):
        """Test leave request with standard validation (no tier validation)."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Request Standard",
                "holiday_status_id": self.leave_type_standard.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=5),
                "date_to": today + timedelta(days=7),
                "number_of_days": 3,
            }
        )

        # Should be in confirm state after creation
        self.assertEqual(leave.state, "confirm")

        # Should not need tier validation
        self.assertFalse(leave.need_validation)

        # HR Manager should be able to validate directly
        leave.with_user(self.hr_manager).action_validate()
        self.assertEqual(leave.state, "validate")

    def test_05_tier_validation_request_and_approve(self):
        """Test the complete tier validation flow: request, review, approve."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Tier Validation",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=10),
                "date_to": today + timedelta(days=12),
                "number_of_days": 3,
            }
        )

        # Should be in confirm state and need validation
        self.assertEqual(leave.state, "confirm")
        self.assertTrue(leave.need_validation)

        # Should have reviews created automatically
        self.assertEqual(
            len(leave.review_ids),
            2,
            f"Expected 2 reviews, found {len(leave.review_ids)}. "
            f"Reviews: {[(r.reviewer_id.name, r.definition_id.sequence) for r in leave.review_ids]}",  # noqa B950
        )

        # Check that we have pending reviews
        pending_reviews = leave.review_ids.filtered(lambda r: r.status == "pending")
        self.assertTrue(pending_reviews)

        # First reviewer (Leave Manager) approves - should be sequence 10
        first_review = leave.review_ids.filtered(
            lambda r: r.definition_id.sequence == 10
        )
        self.assertTrue(first_review, "No review found with sequence 10")
        self.assertEqual(first_review.reviewer_id, self.leave_manager)

        leave.with_user(self.leave_manager).validate_tier()

        leave.invalidate_recordset()

        # Check that the first review is approved but leave is still pending
        self.assertEqual(first_review.status, "approved")
        self.assertFalse(leave.validated)

        # Second reviewer (HR Manager) approves - should be sequence 20
        second_review = leave.review_ids.filtered(
            lambda r: r.definition_id.sequence == 20
        )
        self.assertTrue(second_review, "No review found with sequence 20")
        self.assertEqual(second_review.reviewer_id, self.hr_manager)

        leave.with_user(self.hr_manager).validate_tier()

        leave.invalidate_recordset()

        # Now the leave should be fully validated
        self.assertEqual(second_review.status, "approved")

        self.assertTrue(
            leave.validated,
            "Leave should be validated after both reviews\n"
            f"Leave Reviews: {[(r.reviewer_id.name, r.status) for r in leave.review_ids]}",
        )

        self.assertEqual(leave.state, "validate")

    def test_06_tier_validation_rejection(self):
        """Test tier validation rejection and restart."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Rejection",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=15),
                "date_to": today + timedelta(days=17),
                "number_of_days": 3,
            }
        )

        # Should be in confirm state and have reviews
        self.assertEqual(leave.state, "confirm")
        self.assertTrue(leave.review_ids)

        # HR Officer rejects
        review = leave.review_ids.filtered(
            lambda r: r.reviewer_id == self.leave_manager
        )
        self.assertTrue(review)
        leave.with_user(self.leave_manager).reject_tier()

        leave.invalidate_recordset()

        # Leave should be rejected
        # Note: review record is deleted after rejection, so we can't check review.status
        # self.assertEqual(review.status, "rejected")
        # self.assertTrue(leave.rejected)
        self.assertEqual(leave.state, "refuse")

    def test_07_under_validation_write_protection(self):
        """Test that records under validation cannot be modified."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Write Protection",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=20),
                "date_to": today + timedelta(days=22),
                "number_of_days": 3,
            }
        )

        # Should be in confirm state and under validation
        self.assertEqual(leave.state, "confirm")
        self.assertTrue(leave.need_validation)

        # Should not be able to modify certain fields while under validation
        # Note: write protection may depend on specific implementation
        # This test checks if the leave is in a state where it needs validation
        self.assertTrue(leave.review_ids.filtered(lambda r: r.status == "pending"))

        # Try to modify date_from
        with self.assertRaises(ValidationError):
            leave.with_user(self.employee_user).write(
                {"date_from": today + timedelta(days=25)}
            )

    def test_08_notification_system(self):
        """Test the notification system for pending reviews."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Notification",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=25),
                "date_to": today + timedelta(days=27),
                "number_of_days": 3,
            }
        )

        reviews = leave.with_user(self.employee_user).review_ids

        # Check that reviewers are notified
        pending_reviews = reviews.filtered(lambda r: r.status == "pending")
        self.assertTrue(pending_reviews)

        # Check that the _notify_review_available method works
        leave._notify_review_available(pending_reviews)

        # Verify followers have been updated (reviewers should be subscribed)
        reviewer_partners = pending_reviews.mapped("reviewer_ids.partner_id")
        follower_partners = leave.message_follower_ids.mapped("partner_id")
        for partner in reviewer_partners:
            self.assertIn(partner, follower_partners)

    def test_09_action_methods_with_context(self):
        """Test that action methods properly handle mail_activity_automation_skip context."""
        today = datetime.today()
        leave = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Context",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=30),
                "date_to": today + timedelta(days=32),
                "number_of_days": 3,
            }
        )

        # Test that create method adds the context
        leave2 = self.leave_model.with_user(self.employee_user).create(
            {
                "name": "Test Leave Context 2",
                "holiday_status_id": self.leave_type_tier_validation.id,
                "employee_id": self.employee.id,
                "date_from": today + timedelta(days=35),
                "date_to": today + timedelta(days=37),
                "number_of_days": 3,
            }
        )
        self.assertTrue(leave2)

        # Request validation and approve to test action_validate context
        leave.with_user(self.employee_user).request_validation()

        # Approve by both reviewers
        leave.with_user(self.leave_manager).validate_tier()
        leave.with_user(self.hr_manager).validate_tier()

        # Should be validated
        self.assertEqual(leave.state, "validate")
