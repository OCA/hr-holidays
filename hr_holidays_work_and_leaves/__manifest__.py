# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "hr_holidays_work_and_leaves",
    "summary": "Get real working hours within a period.",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "maintainers": ["NL66278"],
    "website": "https://github.com/OCA/hr-holidays",
    "license": "AGPL-3",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": ["hr_holidays", "hr_holidays_public"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/hr_employee_planning_views.xml",
        "views/hr_employee_views.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "installable": True,
}
