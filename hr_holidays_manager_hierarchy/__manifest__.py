# Copyright 2026 Antoni Marroig (APSL-Nagarro) <antoni.marroig@nagarro.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Time Off Manager Hierarchy",
    "summary": "Managers see and approve the time off of their whole team " "hierarchy",
    "version": "17.0.1.0.0",
    "category": "Human Resources/Time Off",
    "website": "https://github.com/OCA/hr-holidays",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "maintainers": ["peluko00"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["hr_holidays"],
    "data": [
        "security/hr_holidays_security.xml",
        "views/hr_leave_views.xml",
    ],
}
