# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Hr Holidays Allocation Contract Date",
    "summary": """Enforce allocation wizard to have the date at
    least the contract date""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": ["hr_holidays", "hr_contract"],
    "data": [
        "wizards/hr_leave_allocation_generate_multi_wizard.xml",
    ],
    "demo": [],
}
