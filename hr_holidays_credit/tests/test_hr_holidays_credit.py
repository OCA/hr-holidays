# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged

from odoo.addons.hr_holidays.tests.test_negative import TestNegative


@tagged("negative_time_off")
class TestHrHolidaysCredit(TestNegative):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set category and department for some employees
        cls.employee_emp_category_id = cls.env.ref("hr.employee_category_2").id
        cls.employee_hrmanager_category_id = cls.env.ref("hr.employee_category_3").id
        cls.employee_emp.category_ids = [(4, cls.employee_emp_category_id)]
        cls.employee_hrmanager.category_ids = [(4, cls.employee_hrmanager_category_id)]
        cls.employee_emp_department_id = cls.env.ref("hr.dep_administration").id
        cls.employee_hrmanager_department_id = cls.env.ref("hr.dep_rd_ltp").id
        cls.employee_emp.department_id = cls.employee_emp_department_id
        cls.employee_hrmanager.department_id = cls.employee_hrmanager_department_id

    def test_negative_time_off_02(self):
        with freeze_time("2022-10-02"):
            # At the start of 2022, the user receives 1 day, his balance is at 1
            # The first 2022 leave brings the user balance at -4
            self.env["hr.leave"].with_user(self.user_employee_id).create(
                {
                    "name": "first 2022 leave of 5 days",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee_emp.id,
                    "request_date_from": datetime(2022, 10, 24),
                    "request_date_to": datetime(2022, 10, 28),
                }
            )

        with freeze_time("2023-10-02"):
            # At the start of 2023, the user receives 5 days, his balance is at 1
            # The first leave of 2023 brings the balance at -4
            leave = (
                self.env["hr.leave"]
                .with_user(self.user_employee_id)
                .create(
                    {
                        "name": "first 2023 leave of 5 days",
                        "holiday_status_id": self.leave_type.id,
                        "employee_id": self.employee_emp.id,
                        "request_date_from": datetime(2023, 10, 9),
                        "request_date_to": datetime(2023, 10, 13),
                    }
                )
            )

            # We cancel the first leave of 2023, the balance is back at 1
            # Now we don't allow the employee to take negative credit
            # The leave should not be possible to take since this employee is
            # not allowed to take negative credit
            # We are testing the _check_validity() method
            leave._action_user_cancel("Cancel leave")
            self.leave_type.creditable_employee_ids = [(4, self.employee_hrmanager_id)]
            with self.assertRaises(ValidationError):
                self.env["hr.leave"].with_user(self.user_employee_id).create(
                    {
                        "name": "not takable leaves of 5 days",
                        "holiday_status_id": self.leave_type.id,
                        "employee_id": self.employee_emp_id,
                        "request_date_from": datetime(2023, 10, 16),
                        "request_date_to": datetime(2023, 10, 20),
                    }
                )

            # We make the employee be allowed to take negative credit again
            # The leave should be possible to take since it would bring the
            # balance at -4
            self.leave_type.creditable_employee_ids = [(4, self.employee_emp_id)]
            self.env["hr.leave"].with_user(self.user_employee_id).create(
                {
                    "name": "first 2023 leave of 5 days",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee_emp.id,
                    "request_date_from": datetime(2023, 10, 9),
                    "request_date_to": datetime(2023, 10, 13),
                }
            )

    def test_negative_time_off_03(self):
        with freeze_time("2023-10-02"):
            # At the start of 2023, the user receives 5 days
            # The first leave of 2023 brings the balance at 0
            # We are testing the write() method of hr.leave.allocation
            self.env["hr.leave"].with_user(self.user_employee_id).create(
                {
                    "name": "first 2023 leave of 5 days",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee_emp.id,
                    "request_date_from": datetime(2023, 10, 9),
                    "request_date_to": datetime(2023, 10, 13),
                }
            )
            # Now we can change the original allocation to 3 days only
            # The leave should still be possible to take since it would bring
            # the balance at -2
            # Since the employee is allowed to take negative credit
            self.allocation_2023.sudo().write({"number_of_days": 3})
            # We make the employee be not allowed to take negative credit
            # The operation should not be possible since it would bring the
            # balance at -1
            self.leave_type.creditable_employee_ids = [(4, self.employee_hrmanager_id)]
            with self.assertRaises(ValidationError):
                self.allocation_2023.sudo().write({"number_of_days": 4})

    def test_is_holiday_credit_allowed(self):
        self.assertTrue(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee in creditable_employee_ids
        self.leave_type.creditable_employee_ids = [(4, self.employee_emp_id)]
        self.assertTrue(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee not in creditable_employee_ids
        self.leave_type.creditable_employee_ids = [(3, self.employee_emp_id)]
        self.leave_type.creditable_employee_ids = [(4, self.employee_hrmanager_id)]
        self.assertFalse(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee in creditable_employee_category_ids
        self.leave_type.creditable_employee_category_ids = [
            (4, self.employee_emp_category_id)
        ]
        self.assertTrue(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee not in creditable_employee_category_ids
        self.leave_type.creditable_employee_category_ids = [
            (3, self.employee_emp_category_id)
        ]
        self.leave_type.creditable_employee_category_ids = [
            (4, self.employee_hrmanager_category_id)
        ]
        self.assertFalse(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee in creditable_department_ids
        self.leave_type.creditable_department_ids = [
            (4, self.employee_emp_department_id)
        ]
        self.assertTrue(self.leave_type._is_holiday_credit_allowed(self.employee_emp))
        # Employee not in creditable_department_ids
        self.leave_type.creditable_department_ids = [
            (3, self.employee_emp_department_id)
        ]
        self.leave_type.creditable_department_ids = [
            (4, self.employee_hrmanager_department_id)
        ]
        self.assertFalse(self.leave_type._is_holiday_credit_allowed(self.employee_emp))

    def test_get_allocation_data(self):
        # Employee allowed to take negative credit
        result = self.leave_type.get_allocation_data(self.employee_emp)
        self.assertEqual(result[self.employee_emp][0][1]["max_allowed_negative"], 5.0)
        # Employee not allowed to take negative credit
        self.leave_type.creditable_employee_ids = [(4, self.employee_hrmanager_id)]
        result = self.leave_type.get_allocation_data(self.employee_emp)
        self.assertEqual(result[self.employee_emp][0][1]["max_allowed_negative"], 0.0)

    def test_compute_valid(self):
        # At the start of 2023, the user receives 5 days
        with freeze_time("2023-10-02"):
            # The user takes a leave of 6 days (with weekend), his balance is at -1
            # Since the user is allowed to take negative credit up to -5 days,
            # the leave type is valid
            self.env["hr.leave"].with_user(self.user_employee_id).create(
                {
                    "name": "first 2023 leave of 6 days",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": self.employee_emp.id,
                    "request_date_from": datetime(2023, 10, 9),
                    "request_date_to": datetime(2023, 10, 16),
                }
            )
        with freeze_time("2023-10-17"):
            # We check the validity of the leave type for that employee, for past leaves
            # The employee is allowed to take negative credit
            self.leave_type.with_context(
                employee_id=self.employee_emp_id
            )._compute_valid()
            self.assertTrue(self.leave_type.has_valid_allocation)
            # We make the employee be not allowed to take negative credit
            self.leave_type.creditable_employee_ids = [(4, self.employee_hrmanager_id)]
            self.leave_type.with_context(
                employee_id=self.employee_emp_id
            )._compute_valid()
            self.assertFalse(self.leave_type.has_valid_allocation)
