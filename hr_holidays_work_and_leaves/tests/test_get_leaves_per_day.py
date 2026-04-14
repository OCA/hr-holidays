# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime, time

from .common import WorkAndLeavesBase


class TestGetLeavesPerDay(WorkAndLeavesBase):
    def test_two_leaves_returned_in_period(self):
        """_get_leaves_per_day yields an 8-hour and a 4-hour leave in the right order."""
        # Full-day leave: Monday 2026-05-11 09:00–17:00 UTC.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 5, 11, 9, 0, 0),
            datetime(2026, 5, 11, 17, 0, 0),
        )
        # Half-day leave: Wednesday 2026-05-13 09:00–13:00 UTC.
        self._make_validated_leave(
            self.employee,
            datetime(2026, 5, 13, 9, 0, 0),
            datetime(2026, 5, 13, 13, 0, 0),
        )
        start_datetime = datetime(2026, 5, 11, 7, 0, 0)
        end_datetime = datetime(2026, 5, 15, 18, 0, 0)

        leaves = list(self.employee._get_leaves_per_day(start_datetime, end_datetime))

        self.assertEqual(len(leaves), 2)
        first, second = leaves
        self.assertEqual(first.type, "leave")
        self.assertEqual(first.duration, 8.0)
        self.assertEqual(first.datetime_from.date(), date(2026, 5, 11))
        self.assertEqual(first.datetime_from.timetz().replace(tzinfo=None), time(9, 0))
        self.assertEqual(first.datetime_to.timetz().replace(tzinfo=None), time(17, 0))
        self.assertEqual(second.type, "leave")
        self.assertEqual(second.duration, 4.0)
        self.assertEqual(second.datetime_from.date(), date(2026, 5, 13))
        self.assertEqual(second.datetime_from.timetz().replace(tzinfo=None), time(9, 0))
        self.assertEqual(second.datetime_to.timetz().replace(tzinfo=None), time(13, 0))
