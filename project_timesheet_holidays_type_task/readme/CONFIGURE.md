**Prerequisite:** the company-wide internal project and time off task (Settings
→ Time Off) must be configured. Odoo skips timesheet generation entirely when
they are missing, so a time off type would keep its own project without any
effect. They are created automatically and remain the fallback for types
without their own project.

1. Go to *Time Off → Configuration → Time Off Types* and open a time off type.
2. In the *Timesheets* section, set the *Timesheet Project* and optionally the
   *Timesheet Task*.
3. Leave *Timesheet Project* empty to keep the company-wide default for that
   type.

Note: the *Timesheets* section is hidden for types counted as *Worked Time*,
since no timesheets are generated for those.
