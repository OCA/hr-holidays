# Copyright 2024 Moduon Team S.L.
# Copyright 2026 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestResourceCalendarLeaves(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        country = cls.env.company.country_id
        cls.trcl_State = cls.env["res.country.state"].create(
            {
                "name": "TRCL State",
                "code": "TRCL",
                "country_id": country.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "TRCL Partner",
                "country_id": country.id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "TRCL Employee 1",
                "address_id": cls.partner.id,
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
                "state_ids": [Command.set(cls.trcl_State.ids)],
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

    def _create_leave(self):
        leave = self.env["hr.leave"].create(
            {
                "name": "TRCL Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-07-02 23:59:59",
                "employee_id": self.employee.id,
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
        leave = self._create_leave()
        # Leave does not take in consideration State
        self.assertEqual(leave.number_of_days, 2.0)

    def test_leave_partner_with_state(self):
        self.partner.state_id = self.trcl_State
        leave = self._create_leave()
        # Leave takes in consideration State
        self.assertEqual(leave.number_of_days, 1.0)

    def test_validated_leave_new_global_leave(self):
        leave = self._create_leave()
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

    def test_validated_leave_new_local_leave(self):
        self.partner.state_id = self.trcl_State
        leave = self._create_leave()
        self.assertEqual(leave.number_of_days, 1.0)
        other_state = self.trcl_State.copy({"name": "TRCL Other", "code": "TRCLO"})
        # A local holiday from another State must not affect the leave
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Local Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-06-30 23:59:59",
                "state_ids": [(6, 0, other_state.ids)],
                "calendar_id": False,
            }
        )
        self.assertEqual(leave.state, "validate")
        self.assertEqual(leave.number_of_days, 1.0)

    def test_validated_leave_move_global_leave(self):
        leave = self._create_leave()
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
        unusual_days = self.employee._get_unusual_days(
            "2025-07-01 00:00:00", date_to="2025-07-02 23:59:59"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertFalse(unusual_days["2025-07-02"])

    def test_unusual_days_with_state(self):
        self.partner.state_id = self.trcl_State.id
        unusual_days = self.employee._get_unusual_days(
            "2025-07-01 00:00:00", date_to="2025-07-02 23:59:59"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertTrue(unusual_days["2025-07-02"])
