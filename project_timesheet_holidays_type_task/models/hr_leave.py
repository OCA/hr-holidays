from odoo import models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _timesheet_prepare_line_values(
        self, index, work_hours_data, day_date, work_hours_count, project, task
    ):
        self.ensure_one()
        leave_type = self.holiday_status_id
        if leave_type.timesheet_project_id:
            project = leave_type.timesheet_project_id
            task = leave_type.timesheet_task_id
        return super()._timesheet_prepare_line_values(
            index, work_hours_data, day_date, work_hours_count, project, task
        )
