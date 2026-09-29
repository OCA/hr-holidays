# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo.tests.common import tagged

from .common import TestHolidaysPublicResourceCommon


@tagged("post_install", "-at_install")
class TestMultiCompanyMove(TestHolidaysPublicResourceCommon):
    """Moving a public holiday keeps each company's record on its company.

    With ``hr`` installed the working schedule of a time off follows its
    start date, and the company follows the schedule: standard recomputes
    the company whenever the dates change and, on a company-wide record,
    falls back to the current company. The record of every other company
    used to land on the current one and collide with its own record of the
    same line.

    Run after everything is loaded: creating a company needs the defaults
    the timesheet modules add to ``res.company``.
    """

    def test_moving_a_line_keeps_every_company_record(self):
        other = self.env["res.company"].create(
            {"name": "Second Co", "country_id": self.country.id}
        )
        self.env.user.company_ids |= other
        monday = self._work_monday()
        line = self._create_line(monday)
        companies = self.company | other

        def company_record(company):
            return self.leave_model.sudo().search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("calendar_id", "=", False),
                    ("resource_id", "=", False),
                    ("company_id", "=", company.id),
                ]
            )

        before = {company: company_record(company).date_from for company in companies}
        self.assertTrue(all(before.values()))
        line.write({"date": monday + timedelta(days=1)})
        for company in companies:
            record = company_record(company)
            self.assertEqual(len(record), 1)
            self.assertEqual(record.date_from, before[company] + timedelta(days=1))
