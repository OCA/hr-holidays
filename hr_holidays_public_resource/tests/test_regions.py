# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError

from .common import TestHolidaysPublicResourceCommon


class TestRegions(TestHolidaysPublicResourceCommon):
    """Public holidays assigned to regions.

    Some public holidays are observed only in some municipalities --
    Augsburg's Friedensfest, say. A line names the regions it applies to
    and reaches everybody assigned to one of them.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region_augsburg = cls._create_region("Augsburg")
        cls.employee_augsburg = cls._create_employee("Emp Augsburg", cls.calendar_by)
        # The employee follows the public holiday region of the work
        # region; there is nothing to assign on the employee directly.
        cls.employee_augsburg.work_location_id.public_holiday_region_id = (
            cls.region_augsburg
        )

    def _resource_mirror(self, line, employee):
        return self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("resource_id", "=", employee.resource_id.id),
            ]
        )

    def test_a_region_of_another_country_is_left_out(self):
        """The country of the region decides, not the one of the company."""
        abroad = self._create_region("Abroad", country=self.env.ref("base.fr"))
        employee_abroad = self._create_employee("Emp Abroad", self.calendar_by)
        employee_abroad.work_location_id.public_holiday_region_id = abroad
        line = self._create_line(
            self._work_monday(),
            name="Friedensfest",
            regions=self.region_augsburg | abroad,
        )
        self.assertTrue(self._resource_mirror(line, self.employee_augsburg))
        self.assertFalse(
            self._resource_mirror(line, employee_abroad),
            "a German calendar does not apply to a French region",
        )

    def test_region_line_reaches_only_its_employees(self):
        line = self._create_line(
            self._work_monday(),
            name="Friedensfest",
            regions=self.region_augsburg,
        )
        self.assertTrue(self._resource_mirror(line, self.employee_augsburg))
        self.assertFalse(self._resource_mirror(line, self.employee))
        self.assertFalse(self._resource_mirror(line, self.employee_by))
        # A scoped line never lands on a whole schedule.
        self.assertFalse(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("resource_id", "=", False),
                ]
            )
        )

    def test_nationwide_same_day_wins_over_region(self):
        day = self._work_monday()
        region_line = self._create_line(
            day, name="Friedensfest", regions=self.region_augsburg
        )
        national = self._create_line(day, name="National")
        self.assertFalse(self._resource_mirror(region_line, self.employee_augsburg))
        self.assertTrue(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", national.id),
                    ("calendar_id", "=", False),
                    ("company_id", "=", self.company.id),
                ]
            )
        )

    def test_moving_the_employee_moves_the_mirror(self):
        line = self._create_line(
            self._work_monday(),
            name="Friedensfest",
            regions=self.region_augsburg,
        )
        elsewhere_office = self._create_work_location("Elsewhere office", None)
        elsewhere_office.public_holiday_region_id = self._create_region("Elsewhere")
        augsburg_office = self.employee_augsburg.work_location_id
        self.employee_augsburg.work_location_id = elsewhere_office
        self.assertFalse(self._resource_mirror(line, self.employee_augsburg))
        self.employee_augsburg.work_location_id = augsburg_office
        self.assertTrue(self._resource_mirror(line, self.employee_augsburg))

    def test_assignment_from_the_region_side_resyncs(self):
        nowhere = self._create_region("Nowhere")
        line = self._create_line(
            self._work_monday(), name="Friedensfest", regions=nowhere
        )
        self.assertFalse(self._resource_mirror(line, self.employee_augsburg))
        self.region_augsburg.public_holiday_line_ids = [Command.link(line.id)]
        self.assertTrue(self._resource_mirror(line, self.employee_augsburg))
        self.region_augsburg.public_holiday_line_ids = [Command.unlink(line.id)]
        self.assertFalse(self._resource_mirror(line, self.employee_augsburg))

    def test_region_line_is_no_nationwide_duplicate(self):
        day = self._work_monday()
        self._create_line(day, name="National")
        # Must not raise: the scoped line is not a duplicate of the
        # nationwide one on the same date.
        self._create_line(day, name="Friedensfest", regions=self.region_augsburg)

    def test_duplicate_region_on_one_date_raises(self):
        day = self._work_monday()
        self._create_line(day, name="Friedensfest", regions=self.region_augsburg)
        with self.assertRaises(ValidationError):
            self._create_line(day, name="Doubled", regions=self.region_augsburg)

    def test_clearing_the_regions_makes_the_duplicate_visible(self):
        day = self._work_monday()
        self._create_line(day, name="National")
        scoped = self._create_line(
            day, name="Friedensfest", regions=self.region_augsburg
        )
        with self.assertRaises(ValidationError):
            scoped.region_ids = [Command.clear()]

    def test_a_line_that_lost_its_regions_can_be_disabled(self):
        """The escape hatch for a special day whose regions are gone.

        A line scoped only to regions falls back to applying to everybody
        once those regions are deleted -- nothing is left to scope it.
        Disabling the line takes it out of the synchronisation entirely.
        """
        day = self._work_monday()
        line = self._create_line(day, name="Friedensfest", regions=self.region_augsburg)
        # Deleting the region clears the link on the work location, and
        # everybody working there follows.
        self.region_augsburg.unlink()
        line._sync_global_leaves()
        # Without a scope the line is nationwide and reaches every company.
        self.assertTrue(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("calendar_id", "=", False),
                    ("company_id", "=", self.company.id),
                ]
            )
        )
        line.active = False
        self.assertFalse(
            self.leave_model.search([("public_holiday_line_id", "=", line.id)])
        )

    def test_next_year_wizard_carries_the_regions(self):
        line = self._create_line(
            self._work_monday(),
            name="Friedensfest",
            regions=self.region_augsburg,
        )
        self.env["calendar.public.holiday.next.year"].create(
            {"public_holiday_ids": [Command.set(self.holiday.ids)]}
        ).create_public_holidays()
        copy = self.line_model.search(
            [
                ("name", "=", "Friedensfest"),
                ("public_holiday_id.year", "=", self.year + 1),
            ]
        )
        self.assertEqual(len(copy), 1)
        self.assertEqual(copy.region_ids, line.region_ids)
