from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID

from odoo.addons.hr_timesheet.tests.test_timesheet import TestCommonTimesheet


class TestTimesheetHolidaysTypeTask(TestCommonTimesheet):
    def setUp(self):
        super().setUp()
        # from next monday to next wednesday to avoid weekends of the working calendar
        self.leave_start_datetime = datetime(2018, 2, 5)  # this is a monday
        self.leave_end_datetime = self.leave_start_datetime + relativedelta(days=2)

        self.internal_project = self.env.company.internal_project_id
        self.internal_task_leaves = self.env.company.leave_timesheet_task_id

        self.type_project = self.env["project.project"].create(
            {
                "name": "Special Absence Project",
                "allow_timesheets": True,
            }
        )
        self.type_task = self.env["project.task"].create(
            {
                "name": "Special Absence Task",
                "project_id": self.type_project.id,
            }
        )

        self.leave_type_with_task = (
            self.env["hr.leave.type"]
            .sudo()
            .create(
                {
                    "name": "Absence with own project/task",
                    "requires_allocation": False,
                    "timesheet_project_id": self.type_project.id,
                    "timesheet_task_id": self.type_task.id,
                }
            )
        )
        self.leave_type_default = (
            self.env["hr.leave.type"]
            .sudo()
            .create(
                {
                    "name": "Absence with company default",
                    "requires_allocation": False,
                }
            )
        )
        self.Requests = self.env["hr.leave"].with_context(
            mail_create_nolog=True, mail_notrack=True
        )

    def _create_and_validate_leave(self, leave_type):
        leave = self.Requests.with_user(self.user_employee).create(
            {
                "name": "Leave",
                "employee_id": self.empl_employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": self.leave_start_datetime,
                "request_date_to": self.leave_end_datetime,
            }
        )
        leave.with_user(SUPERUSER_ID).action_approve()
        return leave

    def test_timesheets_use_leave_type_project_and_task(self):
        leave = self._create_and_validate_leave(self.leave_type_with_task)
        self.assertTrue(leave.timesheet_ids)
        self.assertEqual(leave.timesheet_ids.project_id, self.type_project)
        self.assertEqual(leave.timesheet_ids.task_id, self.type_task)

    def test_timesheets_fall_back_to_company_default(self):
        leave = self._create_and_validate_leave(self.leave_type_default)
        self.assertTrue(leave.timesheet_ids)
        self.assertEqual(leave.timesheet_ids.project_id, self.internal_project)
        self.assertEqual(leave.timesheet_ids.task_id, self.internal_task_leaves)

    def test_timesheets_use_leave_type_project_without_task(self):
        self.leave_type_with_task.timesheet_task_id = False
        leave = self._create_and_validate_leave(self.leave_type_with_task)
        self.assertTrue(leave.timesheet_ids)
        self.assertEqual(leave.timesheet_ids.project_id, self.type_project)
        self.assertFalse(leave.timesheet_ids.task_id)

    def test_changing_project_resets_task(self):
        other_project = self.env["project.project"].create(
            {
                "name": "Other Project",
                "allow_timesheets": True,
            }
        )
        self.leave_type_with_task.timesheet_project_id = other_project
        self.assertFalse(self.leave_type_with_task.timesheet_task_id)
