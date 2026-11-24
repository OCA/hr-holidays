# Copyright 2026 Daniel Reis <dreis.pt@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Public Holiday Schedule",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "summary": "Generate public holidays into work calendars",
    "website": "https://github.com/OCA/hr-holidays",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "maintainers": ["dreispt"],
    "license": "LGPL-3",
    "depends": ["hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_holiday_schedule_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
