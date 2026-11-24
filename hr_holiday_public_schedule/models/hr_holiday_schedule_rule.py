# Copyright 2026 Daniel Reis <dreis.pt@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re
from calendar import monthrange
from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHolidayRule(models.Model):
    _name = "hr.holiday.schedule.rule"
    _description = "Holiday Rule"
    _order = "schedule_id, sequence, id"

    schedule_id = fields.Many2one(
        "hr.holiday.schedule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    rule_type = fields.Selection(
        [
            ("fixed", "Fixed date"),
            ("easter", "Relative to Easter"),
            ("nth_weekday", "Nth weekday of month"),
            ("custom", "Custom"),
        ],
        required=True,
        default="fixed",
    )
    month = fields.Integer()
    day = fields.Integer()
    easter_offset = fields.Integer(
        default=0,
        help="Days relative to Western Easter Sunday. Good Friday is -2.",
    )
    weekday = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
    )
    ordinal = fields.Selection(
        [
            ("1", "First"),
            ("2", "Second"),
            ("3", "Third"),
            ("4", "Fourth"),
            ("5", "Fifth"),
            ("-1", "Last"),
        ],
        string="Occurrence",
    )
    observed_shift = fields.Selection(
        [
            ("none", "None"),
            ("previous_weekday", "Previous weekday"),
            ("next_weekday", "Next weekday"),
            ("closest_weekday", "Closest weekday"),
        ],
        required=True,
        default="none",
    )
    country_id = fields.Many2one(
        "res.country",
        help="Limit this rule to companies in this country. Must be one of "
        "the schedule countries.",
    )
    state_ids = fields.Many2many(
        "res.country.state",
        help="Limit this rule to employees whose work address is in these states.",
    )
    zip_min = fields.Char()
    zip_max = fields.Char()

    @api.constrains(
        "rule_type",
        "month",
        "day",
        "weekday",
        "ordinal",
        "country_id",
        "state_ids",
        "zip_min",
        "zip_max",
    )
    def _check_rule_fields(self):
        for rule in self:
            if rule.month and not 1 <= rule.month <= 12:
                raise ValidationError(rule.env._("Month must be between 1 and 12."))
            if rule.day and not 1 <= rule.day <= 31:
                raise ValidationError(rule.env._("Day must be between 1 and 31."))
            if rule.rule_type == "fixed" and not (rule.month and rule.day):
                raise ValidationError(
                    rule.env._("Fixed date rules require month and day.")
                )
            if rule.rule_type == "nth_weekday" and not (
                rule.month and rule.weekday and rule.ordinal
            ):
                raise ValidationError(
                    rule.env._(
                        "Nth weekday rules require month, weekday, and occurrence."
                    )
                )
            rule._check_scope_fields()

    def _check_scope_fields(self):
        self.ensure_one()
        schedule_countries = self.schedule_id.country_ids
        if (
            self.country_id
            and schedule_countries
            and self.country_id not in schedule_countries
        ):
            raise ValidationError(
                self.env._("Rule country must be one of the schedule countries.")
            )
        for state in self.state_ids:
            if self.country_id and state.country_id != self.country_id:
                raise ValidationError(
                    self.env._("Rule states must belong to the rule country.")
                )
            if (
                not self.country_id
                and schedule_countries
                and state.country_id not in schedule_countries
            ):
                raise ValidationError(
                    self.env._(
                        "Rule states must belong to one of the schedule countries."
                    )
                )
        if bool(self.zip_min) != bool(self.zip_max):
            raise ValidationError(
                self.env._("Set both Zip Min and Zip Max for a zip range.")
            )
        if (
            self.zip_min
            and self.zip_max
            and self._normalize_zip(self.zip_min) > self._normalize_zip(self.zip_max)
        ):
            raise ValidationError(
                self.env._("Zip Min must be less than or equal to Zip Max.")
            )

    def _compute_holiday_date(self, year):
        self.ensure_one()
        if self.rule_type == "fixed":
            try:
                return date(year, self.month, self.day)
            except (TypeError, ValueError):
                return False
        if self.rule_type == "easter":
            return self._get_easter_sunday(year) + timedelta(
                days=self.easter_offset or 0
            )
        if self.rule_type == "nth_weekday":
            return self._get_nth_weekday_date(year)
        return False

    @staticmethod
    def _get_easter_sunday(year):
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l_val = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l_val) // 451
        month = (h + l_val - 7 * m + 114) // 31
        day = ((h + l_val - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    def _get_nth_weekday_date(self, year):
        self.ensure_one()
        weekday = int(self.weekday)
        first = date(year, self.month, 1)
        first_occurrence = first + timedelta(days=(weekday - first.weekday()) % 7)
        if self.ordinal == "-1":
            last = date(year, self.month, monthrange(year, self.month)[1])
            return last - timedelta(days=(last.weekday() - weekday) % 7)
        candidate = first_occurrence + timedelta(weeks=int(self.ordinal) - 1)
        return candidate if candidate.month == self.month else False

    def _get_observed_date(self, day):
        self.ensure_one()
        if not day or self.observed_shift == "none" or day.weekday() < 5:
            return day
        if self.observed_shift == "previous_weekday":
            return day - timedelta(days=day.weekday() - 4)
        if self.observed_shift == "next_weekday":
            return day + timedelta(days=7 - day.weekday())
        if self.observed_shift == "closest_weekday":
            if day.weekday() == 5:
                return day - timedelta(days=1)
            return day + timedelta(days=1)
        return day

    def _is_scoped(self):
        self.ensure_one()
        return bool(self.state_ids or self.zip_min or self.zip_max)

    def _match_partner(self, partner):
        self.ensure_one()
        if not partner:
            return False
        if self.state_ids and partner.state_id not in self.state_ids:
            return False
        if (self.zip_min or self.zip_max) and not self._zip_matches(partner.zip):
            return False
        return True

    def _zip_matches(self, zip_code):
        self.ensure_one()
        if not (self.zip_min or self.zip_max):
            return True
        normalized = self._normalize_zip(zip_code)
        if not normalized:
            return False
        zip_min = self._normalize_zip(self.zip_min)
        zip_max = self._normalize_zip(self.zip_max)
        return (not zip_min or normalized >= zip_min) and (
            not zip_max or normalized <= zip_max
        )

    @staticmethod
    def _normalize_zip(zip_code):
        return re.sub(r"[^0-9A-Za-z]", "", zip_code or "").upper()
