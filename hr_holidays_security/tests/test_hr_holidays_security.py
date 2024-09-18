# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import SavepointCase

from odoo.addons.mail.tests.common import mail_new_test_user


class HrHolidaysSecurityCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Define some users and their employees
        # responsible 1
        # |- r1 team member A
        # responsible 2
        # |- r2 team member B
        cls.responsible_1 = cls.create_user_and_employee(
            cls, "responsible_1", groups="hr_holidays.group_hr_holidays_responsible"
        )
        cls.responsible_2 = cls.create_user_and_employee(
            cls, "responsible_2", groups="hr_holidays.group_hr_holidays_responsible"
        )
        cls.r1_team_member_a = cls.create_user_and_employee(
            cls, "r1_team_member_a", groups="base.group_user"
        )
        cls.r2_team_member_b = cls.create_user_and_employee(
            cls, "r2_team_member_b", groups="base.group_user"
        )
        cls.r1_team_member_a.employee_id.leave_manager_id = cls.responsible_1
        cls.r2_team_member_b.employee_id.leave_manager_id = cls.responsible_2

    def create_user_and_employee(self, login, groups):
        user = mail_new_test_user(self.env, login=login, groups=groups)
        self.env["hr.employee"].create(
            {
                "name": "Employee %s" % login,
                "user_id": user.id,
            }
        )
        return user

    def test_leave_approvals(self):
        """Different users workflows"""
        # self.env["hr.leave"].search([])
