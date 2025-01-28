# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.hr_holidays_public.tests import test_holidays_calculation


class TestHolidaysComputeDays(test_holidays_calculation.TestHolidaysComputeDays):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.work_location_model = cls.env["hr.work.location"]
        cls.work_location_a = cls.work_location_model.create(
            {
                "name": "Work Location A (ES)",
                "address_id": cls.address_2.id,
            }
        )

        cls.employee_1.write({"address_home_id": cls.address_1.id})
        cls.employee_2.write({"address_home_id": cls.address_2.id})
        cls.employee_2.write({"work_location_id": cls.work_location_a.id})
        cls.public_holiday_country.line_ids.work_location_ids = cls.work_location_a.ids

    # Run all tests of hr_holidays_public
