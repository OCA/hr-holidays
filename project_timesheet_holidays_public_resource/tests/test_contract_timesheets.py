# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestContractTimesheets(TestPublicResourceTimesheetCommon):
    """Public holiday timesheets follow the contract scope.

    A public holiday only concerns somebody employed on that day: no entry
    without a contract, and ending a contract removes the future entries
    beyond its end.
    """

    def _future_line(self):
        day = fields.Date.today() + timedelta(days=7)
        while day.weekday() != 0:
            day += timedelta(days=1)
        holiday = (
            self.holiday
            if day.year == self.year
            else self.holiday_model.create(
                {"year": day.year, "country_id": self.country.id}
            )
        )
        line = self.line_model.create(
            {"name": "Future national", "date": day, "public_holiday_id": holiday.id}
        )
        return line, day

    def test_no_contract_no_timesheet(self):
        casual = self.env["hr.employee"].create(
            {
                "name": "Emp Casual TS",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        line, day = self._future_line()
        self.assertFalse(
            self._lines_for(casual, day),
            "no contract means no public holiday timesheet",
        )
        self.assertTrue(self._lines_for(self.employee, day))

    def test_contract_end_removes_the_future_entries(self):
        line, day = self._future_line()
        self.assertTrue(self._lines_for(self.employee, day))
        self.employee.version_id.contract_date_end = fields.Date.today()
        self.assertFalse(
            self._lines_for(self.employee, day),
            "the day lies beyond the contract end",
        )
        # Extending the contract brings the entry back.
        self.employee.version_id.contract_date_end = day + timedelta(days=30)
        self.assertTrue(self._lines_for(self.employee, day))
