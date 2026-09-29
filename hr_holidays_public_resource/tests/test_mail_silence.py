# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from .common import TestHolidaysPublicResourceCommon


class TestMailSilence(TestHolidaysPublicResourceCommon):
    """Maintaining public holidays never emails anybody.

    The re-evaluation of an overlapping leave rewrites its state and posts
    about days given back or taken; standard notifies the employee (and on a
    refusal the manager) as if somebody had acted. Under the synchronisation
    nobody did, so nothing may leave the system.
    """

    def _mail_count(self):
        return (
            self.env["mail.mail"]
            .sudo()
            .with_context(active_test=False)
            .search_count([])
        )

    def test_adding_and_removing_a_holiday_sends_no_mail(self):
        monday = self._work_monday()
        leave = self._create_leave(self.employee, monday, monday + timedelta(days=4))
        self.assertEqual(leave.number_of_days, 5)
        before = self._mail_count()
        line = self._create_line(monday + timedelta(days=2), name="Mid-week holiday")
        self.assertEqual(leave.number_of_days, 4, "the re-evaluation actually ran")
        self.assertEqual(
            self._mail_count(),
            before,
            "giving the day back emails nobody",
        )
        line.unlink()
        self.assertEqual(leave.number_of_days, 5)
        self.assertEqual(
            self._mail_count(),
            before,
            "taking the day again emails nobody either",
        )
