# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.hr_holidays_public.tests import test_holidays_calculation


class TestHolidaysComputeDays(test_holidays_calculation.TestHolidaysComputeDays):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.es_city_a = cls.env["res.city"].create(
            {
                "name": "Test city A",
                "state_id": cls.env.ref("base.state_es_cr").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.address_2.city_id = cls.es_city_a
        cls.public_holiday_country.line_ids.city_ids = cls.address_2.city_id.ids

    # Run all tests of hr_holidays_public
