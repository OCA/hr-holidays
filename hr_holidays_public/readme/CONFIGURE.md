Go to *Time Off -\> Configuration -\> Time Off Types* and open a Leave
Type

- Leave the standard "Ignore Public Holidays" unchecked to exclude public
  holidays from the leave duration; check it to count them.

Go to *Employees -\> Configuration -\> Work Locations* and open a work
location

- Set its *Public Holiday Region*. Everybody whose contract names this work
  location follows it; the region shows read-only on the employee, on the
  Payroll tab below the working hours. Regions are maintained under
  *Time Off -\> Configuration -\> Public Holidays (OCA) -\> Public Holiday
  Regions*.

Installing the module gives every work location a region of its own, named
after the work location, owned by its company and carrying the country of
its address. Public holidays that were scoped to states before the upgrade
are then assigned to the regions of the work locations whose address lies
in those states; a public holiday whose states no work location lies in is
disabled until it is assigned a region by hand.

The country of a region decides which public holiday calendars apply to the
people assigned to it; the country of the work address only stands in for
an employee without a region, and the company's country for one without a
work address.
