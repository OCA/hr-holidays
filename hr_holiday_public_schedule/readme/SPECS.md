# Public Holiday Schedule - spec

**Status:** implemented
**Date:** 2026-11-24
**Scope:** OCA/hr-holidays, new module `hr_holiday_public_schedule` (LGPL-3)
**Related:** borders core `hr_holidays`/`resource` and the optional AGPL
`hr_holidays_public` stack; this module must not depend on the AGPL stack.

## Context

We need reusable country holiday schedules that materialize native
`resource.calendar.leaves` per company. Core Time Off already subtracts
`resource.calendar.leaves` when computing leave duration, so this module must
not depend on `calendar_public_holiday` or `hr_holidays_public`.

## Spec

- Module `hr_holiday_public_schedule`, LGPL-3, depends on `hr_holidays` only.
- `hr.holiday.schedule` is a reusable template. It has no year catalog of its
  own: `year_to_generate` selects the year to materialize.
- `hr.holiday.schedule` fields: `name`, `active`, `year_to_generate`,
  `country_ids` (m2m `res.country`), `rule_ids`,
  computed `preview`, `action_generate()`, `action_delete_generated()`.
- `hr.holiday.schedule.rule` fields: `schedule_id`, `name`, `sequence`, `active`,
  `rule_type` (`fixed`, `easter`, `nth_weekday`, `custom`),
  `month`, `day`, `easter_offset`, `weekday`, `ordinal`, `observed_shift`
  (`none`, `previous_weekday`, `next_weekday`, `closest_weekday`), and scope
  fields `country_id`, `state_ids`, `zip_min`, `zip_max`.
- `resource.calendar.leaves` gains `hr_holiday_schedule_id`,
  `hr_holiday_rule_id`, and `hr_holiday_year`.
- Generation targets `year_to_generate`. Companies are `res.company` records
  whose `partner_id.country_id` is in `schedule.country_ids`.
- Every active rule generates for every applicable company. To skip a
  discretionary holiday in a given year (for example Carnival), archive the
  rule before generating, or delete the generated leaves afterwards.
- Country-wide rules (no `state_ids` and no zip range) create one company-wide
  leaf per applicable company (`resource_id` empty, `calendar_id` empty).
- Scoped rules create one leaf per matching active employee `resource_id` in
  that company. Scope matching uses the employee work address
  (`address_id`, fallback `work_location_id.address_id`): when `state_ids` is
  set, `partner.state_id` must be included; when a zip range is set, the
  normalized partner zip must be between `zip_min` and `zip_max`.
- Rule dates: `fixed` is `date(year, month, day)` and is skipped when invalid
  (for example Feb 29 outside leap years); `easter` is Western Easter Sunday
  plus `easter_offset`; `nth_weekday` is the nth or last `weekday` of `month`;
  `custom` is computed by overriding `_compute_holiday_date(year)`.
- `observed_shift` moves weekend dates to a weekday. Generated leaves use the
  observed date. `closest_weekday` maps Saturday to Friday and Sunday to
  Monday; `previous_weekday` and `next_weekday` move weekend dates to Friday
  and Monday respectively.
- Leaves are all-day in the company `resource_calendar_id.tz` (fallback UTC),
  `time_type='leave'`, named after the rule, and linked to
  schedule/rule/year.
- Reruns skip leaves already generated for the same
  schedule+rule+company+resource+year+date. `action_delete_generated` removes
  leaves for `year_to_generate`.
- `preview` shows planned leaf counts per company without creating records.

## Contract details

- `hr.holiday.schedule.rule._compute_holiday_date(year)` returns `datetime.date` or
  `False`.
- `hr.holiday.schedule.rule._get_observed_date(day)` returns the shifted date.
- Zip normalization strips non-alphanumerics and uppercases before the range
  comparison.
- `hr.holiday.schedule._get_company_plan(company)` returns the leaf items that
  would be created for that company after applying rule scope, active-rule,
  and idempotency checks.

## Alternatives considered

- OCA `calendar_public_holiday` + `hr_holidays_public`: rejected for this
  module because it is AGPL and catalog-based. It remains available as an
  optional separate stack.
- Yearly catalog line models: rejected. `resource.calendar.leaves` is the
  materialized record and carries the back-pointers.
- A generation wizard: rejected in favor of `year_to_generate` plus
  `action_generate()` on the schedule.

## Tasks

- [x] Implement models, security, and views
- [x] Implement rule date computation and leaf generation
- [x] Add feature tests derived from this spec
- [x] Run lint/module tests on Odoo 19 and review the diff

## Verification

- `pre-commit run --files hr_holiday_public_schedule/**` is green (ruff,
  pylint-odoo, check-xml, generated README/description).
- Odoo 19 module tests pass on a fresh database:
  `hr_holiday_public_schedule` loads and its 5 feature tests report
  `0 failed, 0 error(s)`.
