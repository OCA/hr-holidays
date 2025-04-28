# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT, BaseCommon


class TestResourceCalendarLeaves(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.trcl_State = cls.env["res.country.state"].create(
            {
                "name": "TRCL State",
                "code": "TRCL",
                "country_id": cls.env.user.company_id.country_id.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "TRCL Partner"})
        cls.employee = cls.env["hr.employee"].create(
            {"name": "TRCL Employee 1", "address_id": cls.partner.id}
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
                "state_ids": [(6, 0, cls.trcl_State.ids)],
                "calendar_id": False,
            }
        )
        cls.timeoff_type = cls.env["hr.leave.type"].create(
            {
                "name": "TRCL Time Off",
                "leave_validation_type": "no_validation",
                "requires_allocation": "no",
            }
        )

    def _create_leave(self):
        leave = self.env["hr.leave"].create(
            {
                "name": "TRCL Leave",
                "date_from": "2025-06-30 00:00:00",
                "date_to": "2025-07-02 23:59:59",
                "employee_id": self.employee.id,
                "holiday_status_id": self.timeoff_type.id,
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
        self.partner.state_id = self.trcl_State.id
        leave = self._create_leave()
        # Leave takes in consideration State
        self.assertEqual(leave.number_of_days, 1.0)

    def test_unusual_days_without_state(self):
        unusual_days = self.employee._get_unusual_days(
            "2025-07-01", date_to="2025-07-02"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertFalse(unusual_days["2025-07-02"])

    def test_unusual_days_with_state(self):
        self.partner.state_id = self.trcl_State.id
        unusual_days = self.employee._get_unusual_days(
            "2025-07-01", date_to="2025-07-02"
        )
        self.assertTrue(unusual_days["2025-07-01"])
        self.assertTrue(unusual_days["2025-07-02"])
