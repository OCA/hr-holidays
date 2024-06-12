# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "HR Holidays Remaining Leaves",
    "summary": """
        Show remaining leaves per employee in allocation overview.
    """,
    "author": "Mint System GmbH, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "category": "Human Resources",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_holidays"],
    "data": ["views/hr_leave_allocation.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
