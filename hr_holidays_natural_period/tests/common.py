# Copyright 2020-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import fields
from odoo.tests import new_test_user
from odoo.tools.float_utils import float_compare

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class HrLeaveNaturalPeriodTestMixin:
    """Mixin providing common test utilities for natural period tests."""

    @classmethod
    def setUpClass(cls):
        """Set up minimal shared test data."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.company = cls.env.ref("base.main_company")
        cls.calendar = cls.env.ref("resource.resource_calendar_std")
        cls.env.user.tz = "UTC"

    def _create_natural_day_leave_type(self, **kwargs):
        """Factory method to create a natural day leave type."""
        defaults = {
            "name": kwargs.get("name", "Natural Day Leave"),
            "request_unit": "natural_day",
            "requires_allocation": "no",
        }
        defaults.update(kwargs)
        return self.env["hr.leave.type"].sudo().create(defaults)

    def _create_regular_day_leave_type(self, **kwargs):
        """Factory method to create a regular day leave type."""
        defaults = {
            "name": kwargs.get("name", "Regular Day Leave"),
            "request_unit": "day",
            "requires_allocation": "no",
        }
        defaults.update(kwargs)
        return self.env["hr.leave.type"].sudo().create(defaults)

    def _create_test_employee(self, **kwargs):
        """Factory method to create a test employee with proper setup."""
        partner = (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": kwargs.get("name", "Test Employee"),
                    "type": "other",
                    "country_id": self.env.ref("base.es").id,
                }
            )
        )

        user = new_test_user(
            self.env,
            login=kwargs.get("login", "test-employee"),
            groups="base.group_user,hr.group_hr_user,base.group_partner_manager",
        )

        calendar = kwargs.get("calendar", self.calendar)
        if kwargs.get("copy_calendar", True):
            # Use sudo() for calendar copy to avoid permission issues
            calendar = calendar.sudo().copy({"name": f"Calendar for {partner.name}"})

        defaults = {
            "name": partner.name,
            "address_id": partner.id,
            "resource_calendar_id": calendar.id,
            "user_id": user.id,
        }
        defaults.update(kwargs)
        # Remove helper parameters that aren't employee fields
        defaults.pop("login", None)
        defaults.pop("calendar", None)
        defaults.pop("copy_calendar", None)

        return self.env["hr.employee"].sudo().create(defaults)

    def _create_allocation(self, leave_type, employee, days=10.0, **kwargs):
        """Factory method to create and validate a leave allocation."""
        defaults = {
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "number_of_days": days,
        }
        defaults.update(kwargs)

        allocation = self.env["hr.leave.allocation"].sudo().create(defaults)
        allocation.sudo().action_validate()
        return allocation

    def _create_leave_request(self, leave_type, employee, **kwargs):
        """Factory method to create leave requests with sensible defaults."""
        defaults = {
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "date_from": datetime(2023, 1, 2, 9, 0),
            "date_to": datetime(2023, 1, 4, 17, 0),
            "request_date_from": fields.Date.from_string("2023-01-02"),
            "request_date_to": fields.Date.from_string("2023-01-04"),
        }
        defaults.update(kwargs)
        return self.env["hr.leave"].new(defaults)

    def _create_validated_leave_request(self, leave_type, employee, **kwargs):
        """Factory method to create and validate leave requests."""
        leave_data = {
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "date_from": datetime(2023, 1, 2, 9, 0),
            "date_to": datetime(2023, 1, 4, 17, 0),
            "request_date_from": fields.Date.from_string("2023-01-02"),
            "request_date_to": fields.Date.from_string("2023-01-04"),
        }
        leave_data.update(kwargs)
        # Remove state if it was passed in kwargs
        leave_data.pop("state", None)
        leave = self.env["hr.leave"].sudo().create(leave_data)
        # Validate the leave after creation
        leave.sudo().action_validate()
        return leave

    def _is_module_installed(self, module_name):
        """Check if a module is installed."""
        return bool(
            self.env["ir.module.module"].search(
                [("name", "=", module_name), ("state", "=", "installed")]
            )
        )

    def _assert_duration_equals(self, leave, expected_days, message_suffix=""):
        """Helper to assert leave duration with clear error messages."""
        duration, _ = leave._get_duration()
        message = (
            f"Leave duration should be {expected_days} days, got {duration}. "
            f"Leave type: {leave.holiday_status_id.name}, "
            f"Is natural day: {leave._is_natural_day_leave_type()}"
        )
        if message_suffix:
            message += f". {message_suffix}"

        self.assertEqual(
            float_compare(duration, expected_days, precision_digits=2),
            0,
            message,
        )
