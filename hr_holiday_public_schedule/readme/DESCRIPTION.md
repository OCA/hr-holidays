This module lets you define reusable public holiday schedules and generate
them into native work-calendar leaves.

A schedule lists the countries it applies to and a set of rules: fixed dates,
dates relative to Easter, nth weekday of a month, and custom rules. Rules can
be limited by country, state, or postal code range. Generation writes
`resource.calendar.leaves` for each applicable company, so core Time Off
counts those days without any extra holiday catalog.
