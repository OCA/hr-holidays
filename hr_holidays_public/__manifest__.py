# Copyright 2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# Copyright 2020 InitOS Gmbh
# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "HR Holidays Public",
    "version": "19.0.2.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Michael Telahun Makonnen, "
    "Tecnativa, "
    "Fekete Mihai (Forest and Biomass Services Romania), "
    "Druidoo, "
    "Odoo Community Association (OCA), "
    "glueckkanja AG",
    "summary": "Manage Public Holidays",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": [
        "hr_holidays",
        "calendar_public_holiday",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_work_location_views.xml",
        "views/hr_employee_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/hr_holidays_public_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
