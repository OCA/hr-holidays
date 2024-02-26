# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form, TransactionCase


@freeze_time("2024-01-01")
class TestHrLeaveCalendarEvent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref("base.user_admin")
        cls.leave_type = cls.env.ref("hr_holidays.holiday_status_cl")

    @classmethod
    def _new_leave_request(cls, date_from, date_to):
        leave_form = Form(cls.env["hr.leave"].with_user(cls.admin_user))
        leave_form.holiday_status_id = cls.leave_type
        leave_form.date_from = date_from
        leave_form.date_to = date_to
        return leave_form.save()

    def test_calendar_event_privacy(self):
        self.assertEqual(self.leave_type.calendar_event_privacy, "confidential")
        leave = self._new_leave_request(
            fields.Date.today() + timedelta(days=2),
            fields.Date.today() + timedelta(days=3),
        )
        leave.action_validate()
        self.assertEqual(leave.meeting_id.privacy, "confidential")
        self.leave_type.calendar_event_privacy = "public"
        leave = self._new_leave_request(
            fields.Date.today() + timedelta(days=3),
            fields.Date.today() + timedelta(days=4),
        )
        leave.action_validate()
        self.assertEqual(leave.meeting_id.privacy, "public")
