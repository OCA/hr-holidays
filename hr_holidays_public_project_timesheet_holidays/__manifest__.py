# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "HR Holidays Public Project Timesheet",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Camptocamp, Odoo Community Association (OCA),",
    "summary": "Manage Timesheets for Public Holidays",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": [
        "hr_holidays_public",
        "project_timesheet_holidays",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": True,
}
