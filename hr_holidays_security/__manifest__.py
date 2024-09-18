# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Holidays Security",
    "summary": "Allow time-off responsibles to fully manage their team requests",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Tecnativa, Odoo Community Association (OCA),",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": ["hr_holidays"],
    "data": [
        "security/security.xml",
        "views/hr_leave_views.xml",
        "views/hr_leave_allocation_views.xml",
    ],
    "installable": True,
}
