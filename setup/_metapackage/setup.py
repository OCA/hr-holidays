import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-hr-holidays",
    description="Meta package for oca-hr-holidays Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-hr_holidays_leave_auto_approve>=16.0dev,<16.1dev',
        'odoo-addon-hr_holidays_natural_period>=16.0dev,<16.1dev',
        'odoo-addon-hr_holidays_public>=16.0dev,<16.1dev',
        'odoo-addon-hr_holidays_public_city>=16.0dev,<16.1dev',
        'odoo-addon-hr_leave_type_code>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
