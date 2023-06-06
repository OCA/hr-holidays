# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Holidays Summary Email",
    "summary": """
        Notify employees with daily or weekly leaves summaries of their company.
    """,
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-holidays",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["hr_holidays", "hr_holidays_settings"],
    "data": [
        "data/ir_cron.xml",
        "data/mail_template_data.xml",
        "views/hr_employee_views.xml",
        "views/res_users_views.xml",
        "views/res_config_settings.xml",
    ],
    "maintainers": ["JordiMForgeFlow"],
}
