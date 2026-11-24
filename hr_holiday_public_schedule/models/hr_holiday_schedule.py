# Copyright 2026 Daniel Reis <dreis.pt@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime, time

from pytz import timezone, utc

from odoo import api, fields, models


class HrHolidaySchedule(models.Model):
    _name = "hr.holiday.schedule"
    _description = "Holiday Schedule"
    _order = "name, id"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    year_to_generate = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    country_ids = fields.Many2many(
        "res.country",
        required=True,
        help="Companies in these countries receive the generated holidays.",
    )
    rule_ids = fields.One2many(
        "hr.holiday.schedule.rule",
        "schedule_id",
    )
    preview = fields.Text(compute="_compute_preview")

    @api.depends(
        "year_to_generate",
        "country_ids",
        "rule_ids",
    )
    def _compute_preview(self):
        for schedule in self:
            lines = []
            for company in schedule._get_companies():
                plan = schedule._get_company_plan(company)
                if plan:
                    lines.append(
                        schedule.env._(
                            "%(company)s: %(count)s holiday(s)",
                            company=company.display_name,
                            count=len(plan),
                        )
                    )
            schedule.preview = (
                "\n".join(lines) if lines else schedule.env._("No holidays planned.")
            )

    def action_generate(self):
        self.ensure_one()
        created = self._generate_leaves()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Holiday Schedule"),
                "message": self.env._("Created %s holiday leaves.", created),
                "type": "success",
                "sticky": False,
            },
        }

    def action_delete_generated(self):
        self.ensure_one()
        leaves = self.env["resource.calendar.leaves"].search(
            [
                ("hr_holiday_schedule_id", "=", self.id),
                ("hr_holiday_year", "=", self.year_to_generate),
            ]
        )
        count = len(leaves)
        leaves.unlink()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Holiday Schedule"),
                "message": self.env._("Deleted %s holiday leaves.", count),
                "type": "success",
                "sticky": False,
            },
        }

    def _generate_leaves(self):
        self.ensure_one()
        created = 0
        for company in self._get_companies():
            plan = self._get_company_plan(company)
            if not plan:
                continue
            vals_list = [self._prepare_leave_vals(item) for item in plan]
            self.env["resource.calendar.leaves"].with_company(company).create(vals_list)
            created += len(vals_list)
        return created

    def _prepare_leave_vals(self, item):
        return {
            "name": item["name"],
            "date_from": item["date_from"],
            "date_to": item["date_to"],
            "resource_id": item["resource_id"],
            "time_type": "leave",
            "hr_holiday_schedule_id": self.id,
            "hr_holiday_rule_id": item["rule"].id,
            "hr_holiday_year": self.year_to_generate,
        }

    def _get_companies(self):
        self.ensure_one()
        if not self.country_ids:
            return self.env["res.company"]
        return self.env["res.company"].search(
            [("partner_id.country_id", "in", self.country_ids.ids)]
        )

    def _get_company_plan(self, company):
        self.ensure_one()
        year = self.year_to_generate
        tz_name = company.resource_calendar_id.tz or "UTC"
        existing = self._get_existing_leave_keys(company)
        plan = []
        for rule in self.rule_ids.filtered("active").sorted("sequence"):
            if rule.country_id and rule.country_id != company.country_id:
                continue
            day = rule._compute_holiday_date(year)
            if not day:
                continue
            observed = rule._get_observed_date(day)
            date_from, date_to = self._day_bounds_utc(observed, tz_name)
            if rule._is_scoped():
                for resource in self._get_scoped_resources(rule, company):
                    key = (rule.id, resource.id, date_from)
                    if key in existing:
                        continue
                    plan.append(
                        self._prepare_plan_item(
                            rule, company, resource, observed, date_from, date_to
                        )
                    )
            else:
                key = (rule.id, False, date_from)
                if key in existing:
                    continue
                plan.append(
                    self._prepare_plan_item(
                        rule,
                        company,
                        self.env["resource.resource"],
                        observed,
                        date_from,
                        date_to,
                    )
                )
        return plan

    def _prepare_plan_item(self, rule, company, resource, observed, date_from, date_to):
        return {
            "name": rule.name,
            "rule": rule,
            "company": company,
            "resource_id": resource.id or False,
            "observed_date": observed,
            "date_from": date_from,
            "date_to": date_to,
        }

    def _get_scoped_resources(self, rule, company):
        self.ensure_one()
        employees = self.env["hr.employee"].search(
            [("company_id", "=", company.id), ("active", "=", True)]
        )
        resources = {}
        for employee in employees:
            if not employee.resource_id:
                continue
            partner = self._get_scope_partner(employee)
            if partner and rule._match_partner(partner):
                resources[employee.resource_id.id] = employee.resource_id
        return list(resources.values())

    def _get_scope_partner(self, employee):
        return employee.address_id or employee.work_location_id.address_id

    def _get_existing_leave_keys(self, company):
        self.ensure_one()
        if not isinstance(self.id, int):
            return set()
        leaves = self.env["resource.calendar.leaves"].search(
            [
                ("hr_holiday_schedule_id", "=", self.id),
                ("company_id", "=", company.id),
                ("hr_holiday_year", "=", self.year_to_generate),
            ]
        )
        return {
            (
                leave.hr_holiday_rule_id.id or False,
                leave.resource_id.id or False,
                leave.date_from,
            )
            for leave in leaves
        }

    @staticmethod
    def _day_bounds_utc(day, tz_name):
        tz = timezone(tz_name or "UTC")
        start = tz.localize(datetime.combine(day, time.min))
        end = tz.localize(datetime.combine(day, time.max))
        return (
            start.astimezone(utc).replace(tzinfo=None),
            end.astimezone(utc).replace(tzinfo=None),
        )
