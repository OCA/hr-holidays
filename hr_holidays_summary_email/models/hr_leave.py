# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.model
    def _get_hr_leave_summary_mail_template(self, summary_type):
        return self.env.ref(
            "hr_holidays_summary_email.hr_holidays_summary_mail_template_%s"
            % summary_type,
            raise_if_not_found=False,
        )

    @api.model
    def _get_hr_leave_summary_employee_domain(self, summary_type, company_id):
        return [
            ("hr_leave_summary_type", "=", summary_type),
            ("last_hr_leave_summary_sent", "!=", fields.Date.today()),
            ("company_id", "=", company_id),
        ]

    @api.model
    def _get_hr_leave_summary_base_domain(self, company_id):
        return [
            ("state", "=", "validate"),
            ("employee_id.company_id", "=", company_id),
        ]

    @api.model
    def _get_hr_leave_summary_daily_domain(self, company_id):
        res = self._get_hr_leave_summary_base_domain(company_id)
        res += [
            ("date_from", "<=", fields.Date.today()),
            ("date_to", ">=", fields.Date.today()),
        ]
        return res

    @api.model
    def _get_hr_leave_summary_weekly_domain(self, company_id):
        res = self._get_hr_leave_summary_base_domain(company_id)
        date_from = fields.Date.today()
        date_to = date_from + relativedelta(days=6)
        res += [
            ("date_from", "<=", date_to),
            ("date_to", ">=", date_from),
        ]
        return res

    @api.model
    def _cron_send_hr_leave_summary_emails_daily(self, employees_to_notify, company):
        domain = self._get_hr_leave_summary_daily_domain(company.id)
        today_time_offs = self.env["hr.leave"].sudo().search(domain)
        template = self._get_hr_leave_summary_mail_template("daily")
        if not template:
            return
        for employee in employees_to_notify:
            template.with_context(time_offs=today_time_offs).send_mail(
                employee.id, force_send=False
            )
        employees_to_notify.write({"last_hr_leave_summary_sent": fields.Date.today()})

    @api.model
    def _cron_send_hr_leave_summary_emails_weekly(self, employees_to_notify, company):
        if str(fields.Date.today().weekday()) != company.hr_holidays_summary_weekly_dow:
            return
        domain = self._get_hr_leave_summary_weekly_domain(company.id)
        today_time_offs = self.env["hr.leave"].sudo().search(domain)
        template = self._get_hr_leave_summary_mail_template("weekly")
        if not template:
            return
        for employee in employees_to_notify:
            template.with_context(time_offs=today_time_offs).send_mail(
                employee.id, force_send=False
            )
        employees_to_notify.write({"last_hr_leave_summary_sent": fields.Date.today()})

    @api.model
    def _cron_send_hr_leave_summary_emails(self):
        summary_types = self.env["hr.employee"].fields_get(["hr_leave_summary_type"])[
            "hr_leave_summary_type"
        ]["selection"]
        for company in self.env["res.company"].search([]):
            for stype_tuple in summary_types:
                stype = stype_tuple[0]
                employee_domain = self._get_hr_leave_summary_employee_domain(
                    stype, company.id
                )
                employees_to_notify = self.env["hr.employee"].search(employee_domain)
                if employees_to_notify and hasattr(
                    self, "_cron_send_hr_leave_summary_emails_%s" % stype
                ):
                    getattr(self, "_cron_send_hr_leave_summary_emails_%s" % stype)(
                        employees_to_notify, company
                    )

    def format_hr_leave_summary_date(self, date_from=True):
        self.ensure_one()
        if date_from:
            res = self.date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            res = self.date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.request_unit_half:
            res += (
                " %s"
                % dict(
                    self.env["hr.leave"].fields_get(["request_date_from_period"])[
                        "request_date_from_period"
                    ]["selection"]
                )[self.request_date_from_period]
            )
        elif self.request_unit_hours:
            if date_from:
                res += (
                    " %s"
                    % dict(
                        self.env["hr.leave"].fields_get(["request_hour_from"])[
                            "request_hour_from"
                        ]["selection"]
                    )[self.request_hour_from]
                )
            else:
                res += (
                    " %s"
                    % dict(
                        self.env["hr.leave"].fields_get(["request_hour_to"])[
                            "request_hour_to"
                        ]["selection"]
                    )[self.request_hour_to]
                )
        return res
