# Copyright 2023 CGI (https://www.cgi37.com/)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _prepare_calendar_meeting_leave_name(self, default=""):
        self.ensure_one()
        if self.holiday_status_id.calendar_meeting_leave_template:
            if self.leave_type_request_unit == "hour":
                formatted_duration = _("%.2f hour(s)") % (self.number_of_hours_display,)
            else:
                formatted_duration = _("%.2f day(s)") % (self.number_of_days,)

            return self.holiday_status_id.with_context(
                lang=self.user_id.lang
            ).calendar_meeting_leave_template % {
                "employee_or_category": self.employee_id.name or self.category_id.name,
                "employee_name": self.employee_id.name,
                "category_name": self.category_id.name,
                "formatted_duration": formatted_duration,
                "number_of_hours_display": self.number_of_hours_display,
                "number_of_days": self.number_of_days,
                "start": self.date_from,
                "stop": self.date_to,
                "leave_type_name": self.holiday_status_id.name,
                "leave_type_code": self.holiday_status_id.code,
                "leave_name": self.name,
            }
        return default

    def _prepare_holidays_meeting_values(self):
        result = super()._prepare_holidays_meeting_values()
        # this is a bit annoyed to loop over results
        # and browse leave from it but feel safer and
        # cleaner than overwrite the whole method
        for _user_id, meetings in result.items():
            for meeting_values in meetings:
                leave = self.env["hr.leave"].browse(meeting_values["res_id"]).exists()
                if leave:
                    meeting_values["name"] = leave._prepare_calendar_meeting_leave_name(
                        default=meeting_values["name"]
                    )
        return result
