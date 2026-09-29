# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import TestHolidaysPublicResourceCommon


class TestHrVersionTrigger(TestHolidaysPublicResourceCommon):
    """Contract flows write `hr.version` directly, past the employee.

    The work location and the working schedule live on the version, so a
    version write has to regenerate the personal public holidays right away
    rather than leaving them stale until the nightly synchronisation.
    """

    def _resource_mirror(self, line, employee):
        return self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("resource_id", "=", employee.resource_id.id),
            ]
        )

    def test_writing_the_region_on_the_version_resyncs(self):
        line = self._create_line(
            self._work_monday(), name="Regional", regions=self.region_by
        )
        self.assertFalse(self._resource_mirror(line, self.employee))
        bavarian_office = self._create_work_location("Munich office", self.region_by)
        self.employee.version_id.write({"work_location_id": bavarian_office.id})
        self.assertTrue(self._resource_mirror(line, self.employee))

    def test_writing_the_calendar_on_the_version_resyncs(self):
        line = self._create_line(
            self._work_monday(), name="Regional", regions=self.region_by
        )
        mirror = self._resource_mirror(line, self.employee_by)
        self.assertEqual(mirror.calendar_id, self.calendar_by)
        self.employee_by.version_id.write({"resource_calendar_id": self.calendar.id})
        mirror = self._resource_mirror(line, self.employee_by)
        self.assertEqual(mirror.calendar_id, self.calendar)

    def test_version_write_leaves_nothing_to_update(self):
        line = self._create_line(
            self._work_monday(), name="Regional", regions=self.region_by
        )
        self.employee_by.version_id.write({"resource_calendar_id": self.calendar.id})
        summary = line._sync_global_leaves()
        for key in ("created", "adopted", "updated", "removed"):
            self.assertEqual(summary[key], 0, f"{key} should be 0: {summary}")
