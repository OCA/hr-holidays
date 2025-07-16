# Copyright 2025 APSL-Nagarro Miquel Alzanillas, Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Holidays Public Regional",
    "summary": """
        Manage regional public holidays by assigning dedicated calendars to employees.
        Leaves can optionally exclude regional holidays from their duration calculation.
    """,
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": ["hr_holidays_public"],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/hr_employee.xml",
        "views/hr_holidays_public_regional.xml",
        "views/hr_leave_type.xml",
        "wizards/holidays_public_regional_next_year_wizard.xml",
    ],
    "maintainers": ["peluko00", "miquelalzanillas"],
    "license": "AGPL-3",
    "installable": True,
}
