Whether a leave counts a public holiday is the standard *Ignore Public
Holidays* setting on the leave type, as with `hr_holidays_public` alone.

**Nationwide public holidays** are generated once per company, as a global
time off without working hours that reaches every working schedule of the
company, and they appear in the standard Public Holidays list. A public
holiday line scoped to regions can also name **additional working
schedules**, which get an entry carrying the schedule so that everybody
working by it has the day too -- a regional day observed by one shift plan,
say. A nationwide line needs none: its company-wide record already reaches
every working schedule.

**Region-scoped public holidays** follow the **public holiday region** of
each employee and are generated for that person alone. They are therefore
not in the Public Holidays list, which is company-wide: they show on the
person's own time off calendar, count against their leaves, appear in the
gantt and produce their timesheet entry. Colleagues sharing one working
schedule but working at different regions each get their own.

A public holiday region (*calendar.public.holiday.region*, maintained
under *Configuration > Public Holidays (OCA) > Public Holiday Regions*) is a
plain label of where somebody works -- a state, a plant, the Catholic
municipalities of Bavaria -- carrying the country whose public holiday
calendars apply to it. Every employee carries one, derived by
`hr_holidays_public` from the work location of each version (contract): the
mapping is maintained once, on the work location, and `hr_holidays_public`
bootstraps it on install with one region per work location. A public holiday line names the regions it applies to;
everybody assigned to one of them gets the day, provided the calendar's
country matches the region's. While editing, an empty region cell reads
*All Regions*. The *Create Next Year* copy carries the regions of each line
over to the new year.

A line whose regions are all gone loses its scope and would fall back to
applying to everybody. Disable the line instead of deleting it: it then
generates no time off but keeps its configuration for the day the regions
return. Whether the employees of a schedule get the personal entries of
region-scoped public holidays at all is the *Apply Employee Public
Holidays* setting of the working schedule.

The public holiday region form shows a read-only overview of every public
holiday applying there: the nationwide ones and the ones assigned to it
directly. The working schedule form shows the same kind of overview for the
days that reach the schedule: the nationwide ones of its companies, plus the
region-scoped days resolved from its employees.

The work location and the working schedule of an employee live on their
versions (contracts), and the public holidays follow the version valid on
their day: a contract change in October moves the October holidays to the
new region and schedule without touching the March ones, including for
versions dated in the future. A day no contract covers is given to nobody --
an employee without a contract gets no public holidays at all.

A calendar shown for nobody in particular only shows the nationwide public
holidays as free days, since a region-scoped one belongs to a person.

The public holiday template shows how far it reaches, with a smart button for
the working schedules its nationwide holidays are put on and one for all the
employees it gives a day off.
