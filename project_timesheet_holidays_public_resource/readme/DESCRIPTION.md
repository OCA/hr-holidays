Generates leave timesheet entries for the public holidays that
`hr_holidays_public_resource` creates for a single person.

`project_timesheet_holidays` only timesheets company-wide time off, so a
regional public holiday, which is generated for a single resource, produced
no entry. This bridge module:

- creates a timesheet entry on a regional public holiday for every employee
  it applies to, through the standard generation of public holiday entries
  for an employee, so the entries are indistinguishable from the nationwide
  ones and every extension of that generation applies to them as well;
- back-fills those entries when an employee is hired, reactivated or moved to
  another working schedule;
- skips days that are already covered by a validated leave or another public
  holiday timesheet entry;
- refreshes the future public holiday timesheet entries of everybody on a
  working schedule when its working hours change: removing a day deletes the
  entries of the holidays on it, adding a day creates them. The past is left
  alone, like when an employee switches schedules;
- follows the contract scope: no public holiday entry is created for a day no
  contract of the employee covers, and a contract change -- a new version, an
  ending contract -- rebuilds the employee's future entries accordingly.
  Hand-made global time off keeps its standard behaviour.

The module installs automatically as soon as both
`hr_holidays_public_resource` and `project_timesheet_holidays` are installed.
