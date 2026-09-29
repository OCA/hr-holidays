# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    @api.constrains("date_from", "date_to", "calendar_id")
    def _check_compare_dates(self):
        """Let the generated public holiday mirrors overlap each other.

        The company-wide entry of a nationwide public holiday and the own
        entry a working schedule opts into cover the same day by design, and
        the synchronisation already guarantees one winner per day and scope.
        Standard's constraint treats any same-company overlap as a duplicate,
        so the generated records only check against time off that no
        synchronisation maintains.
        """
        res = None
        mirrors = self.filtered("public_holiday_line_id")
        if self - mirrors:
            res = super(ResourceCalendarLeaves, self - mirrors)._check_compare_dates()
        for record in mirrors.filtered(lambda leave: not leave.resource_id):
            domain = [
                ("resource_id", "=", False),
                ("public_holiday_line_id", "=", False),
                ("company_id", "=", record.company_id.id),
                ("date_from", "<=", record.date_to),
                ("date_to", ">=", record.date_from),
                ("id", "!=", record.id),
            ]
            if record.calendar_id:
                domain.append(("calendar_id", "in", [False, record.calendar_id.id]))
            if self.env["resource.calendar.leaves"].sudo().search_count(domain):
                raise ValidationError(
                    self.env._(
                        "Two public holidays cannot overlap each other for "
                        "the same working hours."
                    )
                )
        return res

    def _get_time_domain_dict(self):
        """Also re-evaluate the leaves a personal public holiday falls into.

        ``hr_holidays`` adjusts the duration of the leaves a global time off
        is created, moved or removed over, but only looks at company-wide
        records. A regional public holiday is generated for the resource of
        each person it concerns, so their approved leaves kept their full
        duration and their allocation was never given back.
        """
        res = super()._get_time_domain_dict()
        res.extend(
            {
                "company_id": record.company_id.id,
                "date_from": record.date_from,
                "date_to": record.date_to,
                "resource_id": record.resource_id.id,
            }
            for record in self
            if record.resource_id and record.public_holiday_line_id
        )
        return res

    def _get_domain(self, time_domain_dict):
        """A personal public holiday only concerns the leaves of its person."""
        personal = [item for item in time_domain_dict if item.get("resource_id")]
        domain = super()._get_domain(
            [item for item in time_domain_dict if not item.get("resource_id")]
        )
        if not personal:
            return domain
        own = Domain.OR(
            Domain("employee_id.resource_id", "=", item["resource_id"])
            & Domain("date_to", ">", item["date_from"])
            & Domain("date_from", "<", item["date_to"])
            for item in personal
        ) & Domain("state", "not in", ["refuse", "cancel"])
        return domain | own

    def _skip_leave_date_check(self, is_global=True):
        """Keep a leave conflict from blocking maintenance of a public holiday.

        ``hr_holidays`` recomputes the leaves a company-wide time off falls
        into whenever one is created, moved or removed, and writing a leave
        runs the overlap constraint. Two overlapping requests already sitting
        in the data therefore surfaced as "An employee already booked time off
        which overlaps with this period" against whatever was being saved --
        adding a public holiday, or deleting one entered by hand.

        The recomputation never moves a leave, so it cannot introduce an
        overlap, and ``leave_skip_date_check`` is what standard itself uses
        wherever it rewrites leaves on the user's behalf. The constraint still
        applies to everyone booking time off.

        This belongs here rather than in ``calendar_public_holiday_resource``:
        that module does not depend on ``hr_holidays`` and therefore sits below
        it in the method resolution order, where the recomputation has already
        run and raised.
        """
        if not is_global or self.env.context.get("leave_skip_date_check"):
            return self
        return self.with_context(leave_skip_date_check=True)

    @api.model_create_multi
    def create(self, vals_list):
        is_global = any(not vals.get("resource_id") for vals in vals_list)
        return super(
            ResourceCalendarLeaves, self._skip_leave_date_check(is_global)
        ).create(vals_list)

    def _has_global_time_off(self):
        return any(not leave.resource_id for leave in self)

    def write(self, vals):
        records = self._skip_leave_date_check(self._has_global_time_off())
        return super(ResourceCalendarLeaves, records).write(vals)

    def unlink(self):
        records = self._skip_leave_date_check(self._has_global_time_off())
        return super(ResourceCalendarLeaves, records).unlink()
