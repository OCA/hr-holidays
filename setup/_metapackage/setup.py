import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-hr-holidays",
    description="Meta package for oca-hr-holidays Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-hr_holidays_natural_period>=15.0dev,<15.1dev',
        'odoo-addon-hr_holidays_public>=15.0dev,<15.1dev',
        'odoo-addon-hr_holidays_public_city>=15.0dev,<15.1dev',
        'odoo-addon-hr_leave_custom_hour_interval>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
