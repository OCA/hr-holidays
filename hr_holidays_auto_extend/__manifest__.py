# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Hr Holidays Auto Extend",
    "summary": """
        Allow to extend some kind of holidays""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": [
        "hr_holidays",
    ],
    "data": [
        "views/hr_leave.xml",
        "views/hr_leave_type.xml",
        "data/cron.xml",
        "data/mail.xml",
    ],
    "demo": [],
}
