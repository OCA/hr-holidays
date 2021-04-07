import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-hr-holidays",
    description="Meta package for oca-hr-holidays Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-hr_holidays_leave_auto_approve',
        'odoo13-addon-hr_holidays_natural_period',
        'odoo13-addon-hr_holidays_public',
        'odoo13-addon-hr_holidays_settings',
        'odoo13-addon-hr_holidays_validity_date',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
