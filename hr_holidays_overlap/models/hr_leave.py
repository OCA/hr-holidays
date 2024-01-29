# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import api, models

exclude_sentinel = object()


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.constrains("date_from", "date_to", "employee_id")
    def _check_date(self):
        """Allow overlapping if the holiday type allows it"""
        return super(
            HrLeave,
            self.with_context(hr_holidays_overlap_exclude=exclude_sentinel).filtered(
                lambda x: not x.holiday_status_id.can_overlap
            ),
        )._check_date()

    @api.model
    def search_count(self, args):
        """Inject condition to exclude leaves whose type allows overlaps if asked so"""
        if self.env.context.get("hr_holidays_overlap_exclude") == exclude_sentinel:
            args += [("holiday_status_id.can_overlap", "=", False)]
        return super().search_count(args)

    def _get_leaves_on_public_holiday(self):
        """Don't count leaves with a type that allows overlap"""
        return (
            super()
            ._get_leaves_on_public_holiday()
            .filtered(lambda x: not x.holiday_status_id.can_overlap)
        )
