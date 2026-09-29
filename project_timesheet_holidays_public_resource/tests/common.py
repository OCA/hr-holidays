# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.hr_holidays_public_resource.tests.common import (
    TestHolidaysPublicResourceCommon,
)


class TestPublicResourceTimesheetCommon(TestHolidaysPublicResourceCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_model = cls.env["account.analytic.line"]
        cls.project = cls.env["project.project"].create(
            {"name": "Internal", "company_id": cls.company.id, "allow_timesheets": True}
        )
        cls.task = cls.env["project.task"].create(
            {"name": "Time Off", "project_id": cls.project.id}
        )
        cls.company.write(
            {
                "internal_project_id": cls.project.id,
                "leave_timesheet_task_id": cls.task.id,
            }
        )

    def _lines_for(self, employee, day):
        return self.analytic_model.search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", day),
                ("global_leave_id", "!=", False),
            ]
        )
