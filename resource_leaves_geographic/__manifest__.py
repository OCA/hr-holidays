# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Resource Leaves Geographic",
    "summary": "Add geographic State to Resource Calendar Leaves",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources/Time Off",
    "website": "https://github.com/OCA/hr-holidays",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "resource",
        "hr_holidays",
    ],
    "data": [
        "views/resource_calendar_leaves_views.xml",
    ],
}
