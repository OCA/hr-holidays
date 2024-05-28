# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "HR Holidays validator list",
    "summary": "Allow to add several leave validators",
    "author": "Victor Vermot, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-holidays",
    "category": "Human Resources",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_holidays"],
    "data": [
        "views/hr_views.xml",
        "views/hr_leave_allocation_views.xml",
        "views/hr_leave_views.xml",
    ],
    "installable": True,
}
