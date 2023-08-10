# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Overtime Visibility in Time Off Dashboard",
    "version": "15.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "license": "AGPL-3",
    "summary": "Make the overtime always visible in the Time Off dashboard",
    "depends": [
        "hr_holidays_attendance",
    ],
    "data": [
        "views/hr_leave_type_views.xml",
    ],
    "installable": True,
}
