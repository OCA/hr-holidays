from odoo import api, fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    timesheet_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Timesheet Project",
        domain="""
            [('company_id', 'in', (company_id, False)),
            ('allow_timesheets', '=', True)]
        """,
        help="""Project on which the timesheets generated for this time off type
are logged. If empty, the internal project of the employee's company is used.""",
    )
    timesheet_task_id = fields.Many2one(
        comodel_name="project.task",
        string="Timesheet Task",
        compute="_compute_timesheet_task_id",
        store=True,
        readonly=False,
        domain="[('project_id', '=', timesheet_project_id)]",
        help="""Task on which the timesheets generated for this time off type are
logged. If empty, the generated timesheets are linked to the project only,
without any task.""",
    )

    @api.depends("timesheet_project_id")
    def _compute_timesheet_task_id(self):
        for leave_type in self:
            if (
                leave_type.timesheet_task_id.project_id
                != leave_type.timesheet_project_id
            ):
                leave_type.timesheet_task_id = False
