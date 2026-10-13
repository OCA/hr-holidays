# Copyright 2026 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tests import common

from odoo.addons.hr_holidays_public_project_timesheet_holidays.hooks import (
    post_init_hook,
)


@freeze_time("2026-06-19")
class TestPublicHolidayTimesheets(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        project = cls.env["project.project"].create(
            {
                "name": "Internal Project PH",
                "company_id": cls.company.id,
                "allow_timesheets": True,
            }
        )
        task = cls.env["project.task"].create(
            {
                "name": "Public Holidays",
                "project_id": project.id,
                "company_id": cls.company.id,
            }
        )
        cls.company.write(
            {
                "internal_project_id": project.id,
                "leave_timesheet_task_id": task.id,
            }
        )

        cls.country_a = cls.env["res.country"].create(
            {"name": "Country A", "code": "XA"}
        )
        cls.country_b = cls.env["res.country"].create(
            {"name": "Country B", "code": "XB"}
        )
        cls.state_a = cls.env["res.country.state"].create(
            {
                "name": "State A",
                "code": "XSA",
                "country_id": cls.country_a.id,
            }
        )

        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Address A",
                "country_id": cls.country_a.id,
            }
        )
        cls.partner_b = cls.env["res.partner"].create(
            {
                "name": "Address B",
                "country_id": cls.country_b.id,
            }
        )
        cls.partner_a_state = cls.env["res.partner"].create(
            {
                "name": "Address A State",
                "country_id": cls.country_a.id,
                "state_id": cls.state_a.id,
            }
        )

        cls.part_time_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Part Time 4h",
                "company_id": cls.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Monday",
                            "dayofweek": "0",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    )
                ],
            }
        )
        cls.flex_calendar = cls.env["resource.calendar"].create(
            {
                "name": "Flex 7h",
                "company_id": cls.company.id,
                "flexible_hours": True,
                "hours_per_day": 7,
                "hours_per_week": 35,
                "full_time_required_hours": 35,
            }
        )

        cls.emp_a = cls.env["hr.employee"].create(
            {
                "name": "Employee A",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.company.resource_calendar_id.id,
                "address_id": cls.partner_a.id,
            }
        )
        cls.emp_b = cls.env["hr.employee"].create(
            {
                "name": "Employee B",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.company.resource_calendar_id.id,
                "address_id": cls.partner_b.id,
            }
        )
        cls.emp_part = cls.env["hr.employee"].create(
            {
                "name": "Employee PT",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.part_time_calendar.id,
                "address_id": cls.partner_a.id,
            }
        )
        cls.emp_flex = cls.env["hr.employee"].create(
            {
                "name": "Employee Flex",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.flex_calendar.id,
                "address_id": cls.partner_a_state.id,
            }
        )

    def _create_public_holiday_line(self, holiday_date, country, state_ids=None):
        public_holiday = self.env["calendar.public.holiday"].create(
            {
                "year": holiday_date.year,
                "country_id": country.id if country else False,
            }
        )
        return self.env["calendar.public.holiday.line"].create(
            {
                "name": f"Holiday {holiday_date}",
                "date": holiday_date,
                "public_holiday_id": public_holiday.id,
                "state_ids": state_ids and [(6, 0, state_ids.ids)] or False,
            }
        )

    def test_create_generates_for_applicable_employees(self):
        """Create a holiday line and generate timesheets only for matching addresses."""
        holiday_date = date(2026, 7, 6)
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        timesheets = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id)
        )

        self.assertIn(self.emp_a, timesheets.employee_id)
        self.assertIn(self.emp_part, timesheets.employee_id)
        self.assertIn(self.emp_flex, timesheets.employee_id)
        self.assertNotIn(self.emp_b, timesheets.employee_id)

    def test_global_holiday_generates_for_all_active_employees(self):
        """A global holiday line (no country) must generate timesheets
        for all employees.
        """
        # Use Monday so the part-time Monday-only employee is included.
        holiday_date = date(2026, 7, 27)
        line = self._create_public_holiday_line(holiday_date, country=False)
        timesheets = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id)
        )

        self.assertIn(self.emp_a, timesheets.employee_id)
        self.assertIn(self.emp_b, timesheets.employee_id)
        self.assertIn(self.emp_part, timesheets.employee_id)
        self.assertIn(self.emp_flex, timesheets.employee_id)

    def test_state_scoped_holiday_only_matches_state(self):
        """A state-scoped holiday must match only employees
        with that state on address.
        """
        holiday_date = date(2026, 7, 23)
        line = self._create_public_holiday_line(
            holiday_date,
            self.country_a,
            state_ids=self.state_a,
        )
        timesheets = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id)
        )

        self.assertIn(self.emp_flex, timesheets.employee_id)
        self.assertNotIn(self.emp_a, timesheets.employee_id)
        self.assertNotIn(self.emp_part, timesheets.employee_id)
        self.assertNotIn(self.emp_b, timesheets.employee_id)

    def test_past_holiday_does_not_generate_timesheets(self):
        """A holiday strictly before today must not generate timesheets."""
        holiday_date = date(2026, 6, 18)
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_today_holiday_generates_timesheets(self):
        """A holiday on today must generate timesheets (date >= today boundary)."""
        holiday_date = fields.Date.today()
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_name_update_does_not_regenerate(self):
        """Renaming a holiday line must keep existing generated timesheets unchanged."""
        holiday_date = date(2026, 7, 7)
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        before_ids = set(
            self.env["account.analytic.line"]
            .search(Domain("public_holiday_line_id", "=", line.id))
            .ids
        )

        line.write({"name": "Renamed"})

        after_ids = set(
            self.env["account.analytic.line"]
            .search(Domain("public_holiday_line_id", "=", line.id))
            .ids
        )
        self.assertEqual(before_ids, after_ids)

    def test_date_update_regenerates(self):
        """Changing the holiday date must delete and recreate
        linked future timesheets.
        """
        line = self._create_public_holiday_line(date(2026, 7, 8), self.country_a)
        old_timesheets = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id)
        )
        self.assertTrue(old_timesheets)

        line.write({"date": date(2026, 7, 9)})
        new_timesheets = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id)
        )

        self.assertTrue(new_timesheets)
        self.assertTrue(all(ts.date == date(2026, 7, 9) for ts in new_timesheets))

    def test_date_update_to_past_deletes_and_does_not_regenerate(self):
        """Changing a future holiday date to the past must delete
        and not recreate timesheets.
        """
        line = self._create_public_holiday_line(date(2026, 7, 24), self.country_a)
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("public_holiday_line_id", "=", line.id)
            )
        )

        line.write({"date": date(2026, 6, 1)})
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_address_change_recomputes_future_timesheets(self):
        """Changing employee address must reassign future timesheets
        to new locality rules.
        """
        line_a = self._create_public_holiday_line(date(2026, 7, 10), self.country_a)
        line_b = self._create_public_holiday_line(date(2026, 7, 10), self.country_b)

        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line_a.id)
            )
        )
        self.emp_a.write({"address_id": self.partner_b.id})

        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line_a.id)
                & Domain("date", ">=", fields.Date.today())
            )
        )
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line_b.id)
            )
        )

    def test_validated_leave_skips_and_refuse_restores(self):
        """Validated leave skips generation, then refusal restores
        missing holiday timesheet.
        """
        holiday_date = date(2026, 7, 13)
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Bridge Leave Type",
                "requires_allocation": False,
            }
        )
        leave = self.env["hr.leave"].create(
            {
                "name": "Leave overlap",
                "employee_id": self.emp_a.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": holiday_date,
                "request_date_to": holiday_date,
            }
        )
        leave.action_approve()

        line = self._create_public_holiday_line(holiday_date, self.country_a)
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

        leave.action_refuse()

        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_validated_leave_skips_and_cancel_restores(self):
        """Validated leave skips generation, then cancellation restores
        missing timesheet.
        """
        holiday_date = date(2026, 7, 28)
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Bridge Leave Type Cancel",
                "requires_allocation": False,
            }
        )
        leave = self.env["hr.leave"].create(
            {
                "name": "Leave overlap cancel",
                "employee_id": self.emp_a.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": holiday_date,
                "request_date_to": holiday_date,
            }
        )
        leave.action_approve()

        line = self._create_public_holiday_line(holiday_date, self.country_a)
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

        leave._action_user_cancel("Cancelled in test")

        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_fixed_calendar_uses_working_hours(self):
        """A fixed calendar employee must get expected working hours
        on a full workday.
        """
        holiday_date = date(2026, 7, 29)
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        timesheet = self.env["account.analytic.line"].search(
            Domain("employee_id", "=", self.emp_a.id)
            & Domain("public_holiday_line_id", "=", line.id),
            limit=1,
        )
        self.assertEqual(timesheet.unit_amount, 8.0)

    def test_part_time_calendar_uses_working_hours(self):
        """A part-time employee must get timesheet hours
        matching calendar attendance.
        """
        # 2026-07-27 is Monday, matching the employee's 08:00-12:00 schedule.
        holiday_date = date(2026, 7, 27)
        line = self._create_public_holiday_line(holiday_date, self.country_a)
        timesheet = self.env["account.analytic.line"].search(
            Domain("employee_id", "=", self.emp_part.id)
            & Domain("public_holiday_line_id", "=", line.id),
            limit=1,
        )
        self.assertEqual(timesheet.unit_amount, 4.0)

    def test_flexible_calendar_uses_hours_per_day(self):
        """Flexible calendars must use hours_per_day as generated timesheet duration."""
        holiday_date = date(2026, 7, 14)
        line = self._create_public_holiday_line(
            holiday_date,
            self.country_a,
            state_ids=self.state_a,
        )
        timesheet = self.env["account.analytic.line"].search(
            Domain("employee_id", "=", self.emp_flex.id)
            & Domain("public_holiday_line_id", "=", line.id),
            limit=1,
        )
        self.assertEqual(timesheet.unit_amount, self.flex_calendar.hours_per_day)

    def test_non_working_day_creates_no_timesheet(self):
        """No timesheet should be generated when the holiday falls
        on a non-working day.
        """
        # 2026-07-12 is a Sunday.
        line = self._create_public_holiday_line(date(2026, 7, 12), self.country_a)
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_manual_deletion_is_blocked(self):
        """Manual unlink of public-holiday-generated timesheets
        must raise a UserError.
        """
        line = self._create_public_holiday_line(date(2026, 7, 15), self.country_a)
        timesheet = self.env["account.analytic.line"].search(
            Domain("public_holiday_line_id", "=", line.id),
            limit=1,
        )

        with self.assertRaises(UserError):
            timesheet.unlink()

    def test_global_leave_timesheet_prevents_duplicate_public_holiday_timesheet(self):
        """Existing global-leave timesheet must prevent creating
        duplicate holiday timesheet.
        """
        holiday_date = date(2026, 7, 16)
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Global Leave",
                "calendar_id": self.company.resource_calendar_id.id,
                "date_from": datetime.combine(holiday_date, datetime.min.time()),
                "date_to": datetime.combine(holiday_date, datetime.max.time()),
            }
        )

        line = self._create_public_holiday_line(holiday_date, self.country_a)
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_salary_simulation_context_skips_creation(self):
        """Employee creation in salary_simulation context
        must not generate holiday timesheets.
        """
        employee = (
            self.env["hr.employee"]
            .with_context(salary_simulation=True)
            .create(
                {
                    "name": "No PH Timesheet",
                    "company_id": self.company.id,
                    "resource_calendar_id": self.company.resource_calendar_id.id,
                    "address_id": self.partner_a.id,
                }
            )
        )
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                [
                    ("employee_id", "=", employee.id),
                    ("public_holiday_line_id", "!=", False),
                ]
            )
        )

    def test_employee_creation_generates_future_public_holiday_timesheets(self):
        """Creating an employee must backfill timesheets
        for future applicable holidays.
        """
        line_a = self._create_public_holiday_line(date(2026, 7, 30), self.country_a)
        line_b = self._create_public_holiday_line(date(2026, 7, 30), self.country_b)

        employee = self.env["hr.employee"].create(
            {
                "name": "Employee Created Later",
                "company_id": self.company.id,
                "resource_calendar_id": self.company.resource_calendar_id.id,
                "address_id": self.partner_a.id,
            }
        )
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", employee.id)
                & Domain("public_holiday_line_id", "=", line_a.id)
            )
        )
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", employee.id)
                & Domain("public_holiday_line_id", "=", line_b.id)
            )
        )

    def test_employee_creation_without_company_config_skips_generation(self):
        """Employee creation must not generate timesheets
        when company mapping is missing.
        """
        self._create_public_holiday_line(date(2026, 7, 31), self.country_a)
        self.company.write(
            {
                "internal_project_id": False,
                "leave_timesheet_task_id": False,
            }
        )

        employee = self.env["hr.employee"].create(
            {
                "name": "No Config Employee",
                "company_id": self.company.id,
                "resource_calendar_id": self.company.resource_calendar_id.id,
                "address_id": self.partner_a.id,
            }
        )
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", employee.id)
                & Domain("public_holiday_line_id", "!=", False)
            )
        )

    def test_archive_then_unarchive_employee(self):
        """Archiving deletes future holiday timesheets; unarchiving regenerates them."""
        # emp_part works only on Mondays in its test calendar.
        line = self._create_public_holiday_line(date(2026, 7, 27), self.country_a)
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_part.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

        self.emp_part.active = False
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_part.id)
                & Domain("public_holiday_line_id", "=", line.id)
                & Domain("date", ">=", fields.Date.today())
            )
        )

        self.emp_part.active = True
        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_part.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

    def test_partner_country_write_does_not_refresh(self):
        """Writing on partner country must not trigger recomputation
        of employee timesheets.
        """
        line = self._create_public_holiday_line(date(2026, 7, 20), self.country_a)
        before = self.env["account.analytic.line"].search_count(
            Domain("employee_id", "=", self.emp_a.id)
            & Domain("public_holiday_line_id", "=", line.id)
        )
        self.partner_a.country_id = self.country_b
        after = self.env["account.analytic.line"].search_count(
            Domain("employee_id", "=", self.emp_a.id)
            & Domain("public_holiday_line_id", "=", line.id)
        )
        self.assertEqual(before, after)

    def test_unlink_holiday_line_keeps_past_timesheet_and_nullifies_link(self):
        """Unlinking a holiday line keeps past timesheets
        and clears their foreign key.
        """
        line = self._create_public_holiday_line(date(2026, 7, 21), self.country_a)
        past_ts = self.env["account.analytic.line"].create(
            {
                "name": "Past PH",
                "project_id": self.company.internal_project_id.id,
                "task_id": self.company.leave_timesheet_task_id.id,
                "account_id": self.company.internal_project_id.account_id.id,
                "unit_amount": 8,
                "user_id": self.env.user.id,
                "date": date(2026, 6, 1),
                "employee_id": self.emp_a.id,
                "company_id": self.company.id,
                "public_holiday_line_id": line.id,
            }
        )

        line.unlink()
        past_ts.invalidate_recordset(["public_holiday_line_id"])
        self.assertTrue(past_ts.exists())
        self.assertFalse(past_ts.public_holiday_line_id)

    def test_generated_timesheet_uses_company_project_and_task(self):
        """Generated timesheet must use the configured company
        internal project and task.
        """
        line = self._create_public_holiday_line(date(2026, 8, 3), self.country_a)
        timesheet = self.env["account.analytic.line"].search(
            Domain("employee_id", "=", self.emp_a.id)
            & Domain("public_holiday_line_id", "=", line.id),
            limit=1,
        )

        self.assertEqual(timesheet.project_id, self.company.internal_project_id)
        self.assertEqual(timesheet.task_id, self.company.leave_timesheet_task_id)

    def test_post_init_hook_backfills_future_timesheets(self):
        """Post-init hook must backfill missing future timesheets for existing data."""
        line = self._create_public_holiday_line(date(2026, 8, 4), self.country_a)
        timesheets = self.env["account.analytic.line"].search(
            Domain("employee_id", "=", self.emp_a.id)
            & Domain("public_holiday_line_id", "=", line.id)
        )
        self.assertTrue(timesheets)

        timesheets.write({"public_holiday_line_id": False})
        timesheets.unlink()
        self.assertFalse(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )

        post_init_hook(self.env)

        self.assertTrue(
            self.env["account.analytic.line"].search_count(
                Domain("employee_id", "=", self.emp_a.id)
                & Domain("public_holiday_line_id", "=", line.id)
            )
        )
