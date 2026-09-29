# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestViews(TransactionCase):
    """Public holidays must be maintained in one place only."""

    def test_standard_public_holiday_list_cannot_create(self):
        view = self.env.ref("hr_holidays.resource_calendar_leaves_tree_inherit")
        self.assertIn(
            'create="0"',
            view.get_combined_arch(),
            "the standard Public Holidays list must not offer to create records",
        )

    def test_standard_public_holiday_action_uses_that_list(self):
        action = self.env.ref("hr_holidays.open_view_public_holiday")
        self.assertEqual(
            action.view_id,
            self.env.ref("hr_holidays.resource_calendar_leaves_tree_inherit"),
            "the create button was disabled on a list this action no longer uses",
        )
