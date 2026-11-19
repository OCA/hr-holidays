# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import Command
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestResourceCalendarLeaves(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        us_country = cls.env.ref("base.us")
        cls.env.company.country_id = us_country
        us_state = cls.env.ref("base.state_us_5")
        cls.partner_without_state = cls.env["res.partner"].create(
            {
                "name": "Test address (without state)",
                "country_id": us_country.id,
            }
        )
        cls.partner_with_state = cls.env["res.partner"].create(
            {
                "name": "Test address (with state)",
                "country_id": us_country.id,
                "state_id": us_state.id,
            }
        )
        cls.employee_a = cls.env["hr.employee"].create(
            {
                "name": "Test Employee (without state)",
                "address_id": cls.partner_without_state.id,
                "contract_date_start": "2025-07-01",
            }
        )
        cls.employee_b = cls.env["hr.employee"].create(
            {
                "name": "Test Employee (with state)",
                "address_id": cls.partner_with_state.id,
                "contract_date_start": "2025-07-01",
            }
        )
        cls.global_leave = cls.env["resource.calendar.leaves"].create(
            {
                "name": "Global Leave",
                "date_from": "2025-07-01 00:00:00",
                "date_to": "2025-07-01 23:59:59",
                "state_ids": False,
                "calendar_id": False,
            }
        )
        cls.local_leave = cls.env["resource.calendar.leaves"].create(
            {
                "name": "Local Leave",
                "date_from": "2025-07-02 00:00:00",
                "date_to": "2025-07-02 23:59:59",
                "state_ids": [Command.set(us_state.ids)],
                "calendar_id": False,
            }
        )
        cls.timeoff_type = cls.env["hr.work.entry.type"].create(
            {
                "name": "TRCL Time Off",
                "code": "TRCL",
                "count_as": "absence",
                "unit_of_measure": "day",
                "leave_validation_type": "no_validation",
                "requires_allocation": False,
            }
        )

    def _create_leave(self, employee):
        leave = self.env["hr.leave"].create(
            {
                "name": "TRCL Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-07-02 23:59:59",
                "employee_id": employee.id,
                "work_entry_type_id": self.timeoff_type.id,
                "request_date_from": "2025-06-30",
                "request_date_to": "2025-07-02",
            }
        )
        if leave.state != "validate":
            leave.action_confirm()
        self.assertEqual(leave.state, "validate")
        return leave

    def test_leave_partner_without_state(self):
        leave = self._create_leave(self.employee_a)
        # Leave does not take in consideration State
        self.assertEqual(leave.number_of_days, 2.0)
        items = self.env["resource.calendar.leaves"].search(
            leave._get_public_holidays_domain(leave.date_to, leave.date_from)
        )
        self.assertIn(self.global_leave, items)
        self.assertNotIn(self.local_leave, items)

    def test_leave_partner_with_state(self):
        leave = self._create_leave(self.employee_b)
        # Leave takes in consideration State
        self.assertEqual(leave.number_of_days, 1.0)
        items = self.env["resource.calendar.leaves"].search(
            leave._get_public_holidays_domain(leave.date_to, leave.date_from)
        )
        self.assertIn(self.global_leave, items)
        self.assertIn(self.local_leave, items)

    def test_leave_multi(self):
        leave_a = self._create_leave(self.employee_a)
        leave_b = self._create_leave(self.employee_b)
        durations = (leave_a | leave_b)._get_durations()
        self.assertEqual(durations[leave_a.id][0], 2.0)
        self.assertEqual(durations[leave_b.id][0], 1.0)

    @mute_logger("odoo.models.unlink")
    def test_validated_leave_new_global_leave(self):
        leave = self._create_leave(self.employee_a)
        self.assertEqual(leave.number_of_days, 2.0)
        # Creating a public holiday re-evaluates overlapping validated leaves
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Global Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-06-30 23:59:59",
                "calendar_id": False,
            }
        )
        self.assertEqual(leave.state, "validate")
        self.assertEqual(leave.number_of_days, 1.0)

    @mute_logger("odoo.models.unlink")
    def test_validated_leave_new_local_leave(self):
        leave = self._create_leave(self.employee_b)
        self.assertEqual(leave.number_of_days, 1.0)
        other_us_state = self.env.ref("base.state_us_10")
        # A local holiday from another State must not affect the leave
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Local Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-06-30 23:59:59",
                "state_ids": [Command.set(other_us_state.ids)],
                "calendar_id": False,
            }
        )
        self.assertEqual(leave.state, "validate")
        self.assertEqual(leave.number_of_days, 1.0)

    @mute_logger("odoo.models.unlink")
    def test_validated_leave_move_global_leave(self):
        leave = self._create_leave(self.employee_a)
        self.assertEqual(leave.number_of_days, 2.0)
        # Moving the public holiday out of the leave gives the day back
        self.global_leave.write(
            {
                "date_from": "2025-07-03 00:00:00",
                "date_to": "2025-07-03 23:59:59",
            }
        )
        self.assertEqual(leave.state, "validate")
        self.assertEqual(leave.number_of_days, 3.0)

    def test_unusual_days_without_state(self):
        unusual_days = self.employee_a._get_unusual_days(
            "2025-07-01 00:00:00", date_to="2025-07-02 23:59:59"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertFalse(unusual_days["2025-07-02"])

    def test_unusual_days_with_state(self):
        unusual_days = self.employee_b._get_unusual_days(
            "2025-07-01 00:00:00", date_to="2025-07-02 23:59:59"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertTrue(unusual_days["2025-07-02"])

    def test_get_public_holidays_without_state(self):
        items = self.employee_a._get_public_holidays("2025-07-01", "2025-07-02")
        self.assertIn(self.global_leave, items)
        self.assertNotIn(self.local_leave, items)

    def test_get_public_holidays_witht_state(self):
        items = self.employee_b._get_public_holidays("2025-07-01", "2025-07-02")
        self.assertIn(self.global_leave, items)
        self.assertIn(self.local_leave, items)
