# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# Copyright 2024- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    repeat_every = fields.Selection(
        [
            ("workday", "Every workday"),
            ("week", "Every week"),
            ("biweek", "Every two weeks"),
            ("month", "Every four weeks"),
        ]
    )
    repeat_mode = fields.Selection(
        [("times", "Number of Times"), ("date", "End Date")], default="times"
    )
    holiday_type_repeat = fields.Boolean(related="holiday_status_id.repeat")
    repeat_limit = fields.Integer(default=1, string="Repeat # times")
    repeat_end_date = fields.Date(default=lambda self: fields.Date.today())

    @api.model
    def _update_repeated_workday_dates(self, resource_calendar, from_dt, to_dt, days):
        user = self.env.user
        from_dt = fields.Datetime.context_timestamp(user, from_dt)
        to_dt = fields.Datetime.context_timestamp(user, to_dt)
        work_hours = resource_calendar.get_work_hours_count(
            from_dt, to_dt, compute_leaves=False
        )
        while work_hours:
            from_dt = from_dt + relativedelta(days=days)
            to_dt = to_dt + relativedelta(days=days)

            new_work_hours = resource_calendar.get_work_hours_count(
                from_dt, to_dt, compute_leaves=True
            )
            if new_work_hours and work_hours <= new_work_hours:
                break

        return from_dt.astimezone(utc).replace(tzinfo=None), to_dt.astimezone(
            utc
        ).replace(tzinfo=None)

    @api.model
    def _get_repeated_vals_dict(self):
        return {
            "workday": {
                "days": 1,
                "user_error_msg": self.env._(
                    "The repetition is based on workdays: the duration of "
                    "the leave request must not exceed 1 day."
                ),
            },
            "week": {
                "days": 7,
                "user_error_msg": self.env._(
                    "The repetition is every week: the duration of the "
                    "leave request must not exceed 1 week."
                ),
            },
            "biweek": {
                "days": 14,
                "user_error_msg": self.env._(
                    "The repetition is every two weeks: the duration of the "
                    "leave request must not exceed 2 weeks."
                ),
            },
            "month": {
                "days": 28,
                "user_error_msg": self.env._(
                    "The repetition is every four weeks: the duration of the "
                    "leave request must not exceed 28 days."
                ),
            },
        }

    @api.model
    def _update_repeated_leave_vals(self, leave, resource_calendar):
        vals_dict = self._get_repeated_vals_dict()
        param_dict = vals_dict[leave.repeat_every]
        from_dt = fields.Datetime.from_string(leave.date_from)
        to_dt = fields.Datetime.from_string(leave.date_to)

        if (to_dt - from_dt).days > param_dict["days"]:
            raise UserError(param_dict["user_error_msg"])

        from_dt, to_dt = self._update_repeated_workday_dates(
            resource_calendar, from_dt, to_dt, param_dict["days"]
        )
        client_tz = timezone(self._context.get("tz") or self.env.user.tz or "UTC")
        request_date_from = utc.localize(from_dt).astimezone(client_tz)
        request_date_to = utc.localize(to_dt).astimezone(client_tz)

        return {
            "employee_id": leave.employee_id.id,
            "date_from": from_dt,
            "date_to": to_dt,
            "request_date_from": request_date_from,
            "request_date_to": request_date_to,
        }

    @api.model
    def create_repeated_handler(self, leave, resource_calendar):
        def _check_repeating(count, leave, date_to):
            repeat_mode = leave.repeat_mode
            if repeat_mode == "times" and count < leave.repeat_limit:
                return True
            if repeat_mode == "date" and date_to.date() <= leave.repeat_end_date:
                return True
            return False

        count = 1
        leaves = self.env["hr.leave"]
        vals = self._update_repeated_leave_vals(leave, resource_calendar)
        while _check_repeating(count, leave, vals.get("date_to")):
            leave = leave.with_context(skip_create_handler=True).copy(vals)
            leaves += leave
            count += 1
            vals = self._update_repeated_leave_vals(leave, resource_calendar)
        return leaves

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        skip_create_handler = self.env.context.get("skip_create_handler")
        if skip_create_handler:
            return res
        for leave in res.filtered(
            lambda leave: leave.repeat_every and leave.repeat_mode
        ):
            resource_calendar = leave.resource_calendar_id
            res += self.create_repeated_handler(leave, resource_calendar)
        return res

    @api.constrains("repeat_mode", "repeat_limit", "repeat_end_date")
    def _check_repeat_limit(self):
        for record in self:
            if record.repeat_mode == "times" and record.repeat_limit < 0:
                raise ValidationError(
                    self.env._("Please set a positive amount of repetitions.")
                )
            if (
                record.repeat_mode == "date"
                and record.repeat_end_date < record.date_from.date()
            ):
                raise ValidationError(
                    self.env._("The Repeat End Date cannot be before the leave.")
                )
