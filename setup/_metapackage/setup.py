import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-hr-holidays",
    description="Meta package for oca-hr-holidays Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_holidays_credit',
        'odoo14-addon-hr_holidays_leave_auto_approve',
        'odoo14-addon-hr_holidays_natural_period',
        'odoo14-addon-hr_holidays_public',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
