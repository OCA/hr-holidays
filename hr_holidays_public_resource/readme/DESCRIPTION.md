Makes the standard Odoo time off machinery use the public holidays configured
in the public holiday calendar, instead of a parallel implementation.

`calendar_public_holiday_resource` materialises every public holiday as time
off, which is what standard Odoo keys all of its public holiday behaviour on.
This module adds the HR side of that integration:

- public holidays are excluded from the duration of a leave, controlled by the
  standard *Ignore Public Holidays* setting of the leave type;
- they are greyed out as unusual days in the time off calendar and shown as
  unavailable in gantt views;
- leaves and timesheets that were already approved are recomputed when a public
  holiday is added, moved or removed;
- with `project_timesheet_holidays` installed, a timesheet entry is generated on
  a public holiday for every employee it applies to -- the per-person part of
  this is provided by the `project_timesheet_holidays_public_resource` bridge
  module, which installs automatically;
- region-scoped public holidays are resolved to the employees assigned to
  one of the regions -- the public holiday region `hr_holidays_public`
  derives from the work location of their contract -- so that colleagues
  sharing a working schedule keep their own.

`hr_holidays_public` on its own takes public holidays out of the working
time through a private `_attendance_intervals_batch` override that no
standard module is aware of. This module switches that engine off: the
generated time off is what standard excludes, keyed on the same *Ignore
Public Holidays* setting of the leave type.
