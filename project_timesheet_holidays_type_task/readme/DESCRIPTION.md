Reintroduces the per-time-off-type timesheet configuration known from earlier Odoo versions.

Adds a *Timesheet Project* and *Timesheet Task* field on the time off type form. When a time off of that type is validated and the type has a project configured, the generated timesheet lines are logged on that project and task instead of the company-wide internal project and time off task configured in `project_timesheet_holidays`. Time off types without their own project keep using the company default.
