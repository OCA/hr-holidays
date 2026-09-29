# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields

from .common import TestHolidaysPublicResourceCommon


class TestUnusualDaysWithoutEmployee(TestHolidaysPublicResourceCommon):
    """An administrator switching companies must still see the real calendar.

    ``res.users.employee_id`` is company dependent, so with a company the user
    has no employee record in it resolves to nothing, and standard
    ``hr.employee._get_unusual_days`` then finds no contract version and marks
    every single day as unusual -- the whole time off calendar looks like one
    long holiday and the public holidays cannot be told apart.
    """

    def setUp(self):
        super().setUp()
        self.monday = self._work_monday()
        self.wednesday = self.monday + timedelta(days=2)
        self.sunday = self.monday - timedelta(days=1)

    def _unusual_days(self):
        return self.env["hr.leave"].get_unusual_days(
            f"{self.sunday} 00:00:00",
            f"{self.monday + timedelta(days=4)} 23:59:59",
        )

    def _drop_user_employees(self):
        """Reproduce a company the current user has no employee record in."""
        self.env.user.employee_ids.unlink()
        self.assertFalse(self.env.user.employee_id)

    def test_no_employee_still_reports_working_days(self):
        self._drop_user_employees()
        self.assertFalse(
            self._unusual_days()[fields.Date.to_string(self.wednesday)],
            "a plain working day must not be reported as free",
        )

    def test_no_employee_still_reports_weekends(self):
        self._drop_user_employees()
        self.assertTrue(self._unusual_days()[fields.Date.to_string(self.sunday)])

    def test_no_employee_still_reports_public_holidays(self):
        self._drop_user_employees()
        self._create_line(self.wednesday, name="Mid-week holiday")
        self.assertTrue(
            self._unusual_days()[fields.Date.to_string(self.wednesday)],
            "the public holiday must still be greyed out",
        )

    def test_company_without_working_schedule_falls_back_to_standard(self):
        self._drop_user_employees()
        self.company.resource_calendar_id = False
        # Nothing to go by any more, so the standard answer stands.
        self.assertTrue(self._unusual_days()[fields.Date.to_string(self.wednesday)])

    def test_employee_of_the_active_company_still_wins(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Admin Employee",
                "user_id": self.env.user.id,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
                "date_version": f"{self.year - 1}-01-01",
                "contract_date_start": f"{self.year - 1}-01-01",
            }
        )
        self.assertEqual(self.env.user.employee_id, employee)
        self.assertFalse(self._unusual_days()[fields.Date.to_string(self.wednesday)])
