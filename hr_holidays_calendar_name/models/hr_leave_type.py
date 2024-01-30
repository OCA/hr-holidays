# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    calendar_meeting_leave_template = fields.Char(
        translate=True,
        help=(
            "Template used to generate calendar meeting name, \n"
            "ie: '%(employee_name)s on Time Off : %(formatted_duration)s' which is roughly "
            "the default behavior from odoo if you leave this field empty."
            "Here the list of possible parameters: \n"
            "* `employee_or_category`: employee name or category if leave has no users "
            "linked\n"
            "* `employee_name`: employee name\n"
            "* `category_name`: hr category name (tag)\n"
            "* `formatted_duration`: number of ours or days with the unit according the "
            "kind of leave\n"
            "* `number_of_hours_display`: number of hours\n"
            "* `number_of_days`: number of days\n"
            "* `start`: start date\n"
            "* `stop`: end date\n"
            "* `leave_type_name`: leave type name\n"
            "* `leave_type_code`: leave type code\n"
            "* `leave_name`: leave name\n"
        ),
    )
