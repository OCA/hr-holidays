# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command

from .common import TestHolidaysPublicResourceCommon


class TestRegionOverview(TestHolidaysPublicResourceCommon):
    """The read-only overview on the public holiday region form.

    A union of everything somebody assigned to the region gets: the
    nationwide public holidays and the ones assigned to it directly.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region = cls._create_region(
            "Augsburg", company=cls.company, country=cls.country
        )
        cls.region_plain = cls._create_region(
            "Elsewhere", company=cls.company, country=cls.country
        )
        day = cls._work_monday()
        cls.line_national = cls._create_line(day, name="National")
        cls.line_direct = cls._create_line(
            day + timedelta(days=1), name="Friedensfest", regions=cls.region
        )

    def _overview(self, region):
        region.invalidate_recordset(["public_holiday_overview_line_ids"])
        return region.public_holiday_overview_line_ids

    def test_nationwide_shows_everywhere(self):
        self.assertIn(self.line_national, self._overview(self.region))
        self.assertIn(self.line_national, self._overview(self.region_plain))

    def test_direct_assignment_shows_only_there(self):
        self.assertIn(self.line_direct, self._overview(self.region))
        self.assertNotIn(self.line_direct, self._overview(self.region_plain))

    def test_assignment_change_updates_the_overview(self):
        self.line_direct.region_ids = [Command.link(self.region_plain.id)]
        self.assertIn(self.line_direct, self._overview(self.region_plain))

    def test_foreign_country_is_ruled_out(self):
        foreign = self.line_model.create(
            {
                "name": "Foreign national",
                "date": self._work_monday() + timedelta(days=2),
                "public_holiday_id": self.holiday_model.create(
                    {"year": self.year, "country_id": self.env.ref("base.fr").id}
                ).id,
            }
        )
        self.assertNotIn(foreign, self._overview(self.region))

    def test_a_region_without_a_country_sees_everything(self):
        """An unknown country cannot rule a holiday calendar out."""
        shared = self._create_region("Shared")
        self.assertIn(self.line_national, self._overview(shared))

    def test_overview_is_readonly(self):
        field = self.env["calendar.public.holiday.region"]._fields[
            "public_holiday_overview_line_ids"
        ]
        self.assertTrue(field.compute)
        self.assertTrue(field.readonly)
        self.assertFalse(field.store)
