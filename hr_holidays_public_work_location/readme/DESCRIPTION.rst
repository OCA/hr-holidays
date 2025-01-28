This module adds the work location of employees at the public vacation line
level as an extra discriminant. That way, we can have some public vacations
that are only valid for employees working in a specific location, even when
there are more locations in the same country or state.

The chosen work locations must belong to the public vacation's country, as well
as public vacation line's state, if any. That information is stored in the work
location's address.
