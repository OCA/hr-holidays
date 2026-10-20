By default, only the direct time off approver of an employee (the *Time Off*
field on the employee) can see and approve their time off requests. Managers
higher up in the hierarchy have no access to them.

This module extends that access in cascade through the employee hierarchy
(*Manager* field): a time off responsible can see, approve and refuse the time
off requests of every employee below them, at any depth.

Managers in the hierarchy get exactly the same rights as the direct approver:

- Time off types validated by the Time Off Officer still require an officer.
- Nobody can approve their own requests.

The *Approve* and *Refuse* buttons of the time off list and kanban views are
only shown when the user can actually approve the request, as the form view
already does, and the *Validate* button (second approval) is only shown to
Time Off Officers, the only ones allowed to use it.
