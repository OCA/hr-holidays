{
    "name": "HR holidays tier validation",
    "version": "16.0.1.0.0",
    "category": "Human Resources",
    "summary": "Tier Validation for HR Holidays",
    "author": "Odoo Community Association (OCA), OpenStudio SAS",
    "website": "https://github.com/OCA/hr-holidays",
    "depends": [
        "hr_holidays",
        "base_automation",
        "base_tier_validation",
        "base_tier_validation_waiting",  # To alert only the next approver
        "base_tier_validation_allow_disable_restart",  # To avoid breaking the flow
    ],
    "data": [
        "views/hr_leave_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
