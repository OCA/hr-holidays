# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Time Off Approval Split",
    "summary": """
        Allow configuring approval requirements separately for hour-based and
        day-based time off requests.
    """,
    "category": "Human Resources/Time Off",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "contributors": [
        "Guillermo Navas <guillermo.navas@forgeflow.com>",
    ],
    "depends": ["hr_holidays"],
    "data": [
        "views/hr_leave_type_views.xml",
    ],
}
