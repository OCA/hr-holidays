from odoo.tests.common import SavepointCase


class TestHrLeaveComulativeFields(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.HrLeave = cls.env["hr.leave"]
        cls.HrLeaveAllocation = cls.env["hr.leave.allocation"]
        cls.HrLeaveType = cls.env["hr.leave.type"]

        cls.employee = cls.env.ref("hr.employee_qdp")

        cls.custom_hr_leave_type = cls.HrLeaveType.create(
            [
                {
                    "name": "Custom Leave Type",
                    "request_unit": "day",
                    "allocation_type": "fixed",
                    "leave_validation_type": "hr",
                }
            ]
        )

    def test_cumulative_time_off_values(self):
        allocation_1 = self.HrLeaveAllocation.create(
            [
                {
                    "name": "New Allocation for Marc Demo",
                    "holiday_type": "employee",
                    "employee_id": self.employee.id,
                    "holiday_status_id": self.custom_hr_leave_type.id,
                    "allocation_type": "regular",
                    "number_of_days": 7,
                }
            ]
        )
        allocation_1.action_approve()
        starting_leave = self.HrLeave.create(
            [
                {
                    "employee_id": self.employee.id,
                    "holiday_status_id": self.custom_hr_leave_type.id,
                    "holiday_type": "employee",
                    "date_from": "2024-06-03",
                    "date_to": "2024-06-08",
                },
            ]
        )

        self.assertEqual(starting_leave.cumulative_used_timeoff, 5)
        self.assertEqual(starting_leave.cumulative_remaining_timeoff, 2)

        allocation_2 = self.HrLeaveAllocation.create(
            [
                {
                    "name": "New Allocation for Marc Demo",
                    "holiday_type": "employee",
                    "employee_id": self.employee.id,
                    "holiday_status_id": self.custom_hr_leave_type.id,
                    "allocation_type": "regular",
                    "number_of_days": 20,
                }
            ]
        )
        allocation_2.action_approve()

        self.assertEqual(starting_leave.cumulative_used_timeoff, 5)
        self.assertEqual(starting_leave.cumulative_remaining_timeoff, 22)

        latest_leave = self.HrLeave.create(
            [
                {
                    "employee_id": self.employee.id,
                    "holiday_status_id": self.custom_hr_leave_type.id,
                    "holiday_type": "employee",
                    "date_from": "2024-06-17",
                    "date_to": "2024-06-22",
                },
            ]
        )

        self.assertEqual(starting_leave.cumulative_used_timeoff, 5)
        self.assertEqual(starting_leave.cumulative_remaining_timeoff, 22)

        self.assertEqual(latest_leave.cumulative_used_timeoff, 10)
        self.assertEqual(latest_leave.cumulative_remaining_timeoff, 17)
