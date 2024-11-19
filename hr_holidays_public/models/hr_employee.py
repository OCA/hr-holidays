from odoo import fields, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    def _get_unusual_days(self, date_from, date_to=None):
        res = super()._get_unusual_days(date_from, date_to=date_to)
        if not self:
            return res
        domain = self.env["hr.leave"]._get_domain_from_get_unusual_days(
            date_from=date_from, date_to=date_to
        )
        public_holidays = self.env["hr.holidays.public.line"].search(domain)
        for public_holiday in public_holidays:
            res[fields.Date.to_string(public_holiday.date)] = True
        return res
