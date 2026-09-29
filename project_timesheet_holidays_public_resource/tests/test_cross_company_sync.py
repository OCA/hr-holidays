# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests.common import tagged

from .common import TestPublicResourceTimesheetCommon


@tagged("post_install", "-at_install")
class TestCrossCompanySync(TestPublicResourceTimesheetCommon):
    """The sync may touch companies outside the user's selection.

    Saving the first employee of a new company resynchronises their working
    schedule; on a shared schedule that legitimately cleans up another
    company's mirrors, whose overlapping leaves then get their timesheets
    regenerated. ``hr_timesheet`` refuses an employee outside
    ``env.companies``, so the sync selects the companies it acts on itself --
    without that, creating the employee failed with "Timesheets must be
    created with an active employee in the selected companies".
    """

    def test_first_employee_may_clean_another_company_mirror(self):
        day = self._work_monday()
        line = self._create_line(day, name="National")
        shared = self.env["resource.calendar"].create(
            {"name": "Shared cross-company", "company_id": False, "tz": "Europe/Berlin"}
        )
        company_c = self.env["res.company"].create(
            {"name": "Other Co", "country_id": self.country.id}
        )
        env_c = self.env(
            context=dict(self.env.context, allowed_company_ids=[company_c.id])
        )
        employee_c = env_c["hr.employee"].create(
            {
                "name": "Emp Other",
                "company_id": company_c.id,
                "resource_calendar_id": shared.id,
                "date_version": f"{self.year - 1}-01-01",
                "contract_date_start": f"{self.year - 1}-01-01",
            }
        )
        leave_type_c = env_c["hr.leave.type"].create(
            {
                "name": "PTO Other",
                "requires_allocation": False,
                "leave_validation_type": "no_validation",
                "request_unit": "day",
                "company_id": company_c.id,
            }
        )
        env_c["hr.leave"].create(
            {
                "name": "Vacation",
                "employee_id": employee_c.id,
                "holiday_status_id": leave_type_c.id,
                "request_date_from": day,
                "request_date_to": day + timedelta(days=2),
            }
        )
        # A leftover per-schedule mirror, as an unmigrated database holds.
        stale = (
            self.leave_model.sudo()
            .with_context(public_holiday_sync=True, leave_skip_date_check=True)
            .with_company(company_c)
            .create(
                {
                    "name": line.name,
                    "calendar_id": shared.id,
                    "time_type": "leave",
                    "date_from": datetime(day.year, day.month, day.day, 0, 0),
                    "date_to": datetime(day.year, day.month, day.day, 23, 59, 59),
                    "public_holiday_line_id": line.id,
                }
            )
        )
        stale.write({"company_id": company_c.id})

        company_b = self.env["res.company"].create(
            {"name": "New Co", "country_id": self.country.id}
        )
        env_b = self.env(
            context=dict(self.env.context, allowed_company_ids=[company_b.id])
        )
        employee_b = env_b["hr.employee"].create(
            {
                "name": "First Employee",
                "company_id": company_b.id,
                "resource_calendar_id": shared.id,
            }
        )
        self.assertTrue(employee_b.exists())
        self.assertFalse(
            stale.exists(),
            "the other company's leftover mirror is cleaned up along the way",
        )
