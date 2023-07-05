from odoo.tests.common import TransactionCase


class TestHolidaysType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HrLeaveType = cls.env["hr.leave.type"]

    def test_name_get_no_code(self):
        name = "test"
        leave = self.HrLeaveType.create({"name": name})
        self.assertEqual(leave.display_name, name)

    def test_name_get_code(self):
        name = "test"
        code = "123"
        leave = self.HrLeaveType.create({"name": name, "code": code})
        self.assertEqual(leave.display_name, f"{code} - {name}")
