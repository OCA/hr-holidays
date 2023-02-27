# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Hr holidays calendar events privacy",
    "summary": "Define privacy level of calendar events from Time off requests",
    "version": "15.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-holidays",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["grindtildeath"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_holidays",
    ],
    "data": [
        "views/hr_leave_type.xml",
    ],
}
