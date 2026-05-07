# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, datetime

from .common import WorkAndLeavesBase


class TestHrEmployeePlanning(WorkAndLeavesBase):
    def _create_wizard(self, employee, date_start, date_end):
        return self.env["hr.employee.planning"].create(
            {
                "employee_id": employee.id,
                "date_start": date_start,
                "date_end": date_end,
            }
        )

    def test_action_show_planning_opens_wizard(self):
        """action_show_planning creates a wizard for the employee and returns its action."""
        action = self.employee.action_show_planning()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "hr.employee.planning")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")
        wizard = self.env["hr.employee.planning"].browse(action["res_id"])
        self.assertEqual(wizard.employee_id, self.employee)

    def test_even_week_full_and_partial_leave(self):
        """Even week: full Mon leave + Fri half-day leave → 5 lines with correct hours."""
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 11, 9, 0, 0),
            datetime(2026, 5, 11, 17, 0, 0),
        )
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 15, 11, 0, 0),
            datetime(2026, 5, 15, 13, 0, 0),
            full_day=False,
        )
        wizard = self._create_wizard(
            self.employee_two_week, date(2026, 5, 11), date(2026, 5, 15)
        )
        wizard.action_compute()

        lines = wizard.planning_line_ids.sorted("date")
        self.assertEqual(len(lines), 5)
        # Monday: full-day leave, no work.
        self.assertEqual(lines[0].date, date(2026, 5, 11))
        self.assertAlmostEqual(lines[0].hours_work, 0.0)
        self.assertAlmostEqual(lines[0].hours_leave, 8.0)
        self.assertAlmostEqual(lines[0].hours_holiday, 0.0)
        # Tuesday through Thursday: full work days.
        for idx, day in enumerate([12, 13, 14], start=1):
            self.assertEqual(lines[idx].date, date(2026, 5, day))
            self.assertAlmostEqual(lines[idx].hours_work, 8.0)
            self.assertAlmostEqual(lines[idx].hours_leave, 0.0)
            self.assertAlmostEqual(lines[idx].hours_holiday, 0.0)
        # Friday: 6h work split around the 2h half-day leave.
        self.assertEqual(lines[4].date, date(2026, 5, 15))
        self.assertAlmostEqual(lines[4].hours_work, 6.0)
        self.assertAlmostEqual(lines[4].hours_leave, 2.0)
        self.assertAlmostEqual(lines[4].hours_holiday, 0.0)

    def test_odd_week_spanning_leave(self):
        """Odd week (Mon off): leave Fri–Wed → 4 lines, Tue/Wed leave, Thu/Fri work."""
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 15, 9, 0, 0),
            datetime(2026, 5, 20, 17, 0, 0),
        )
        wizard = self._create_wizard(
            self.employee_two_week, date(2026, 5, 18), date(2026, 5, 22)
        )
        wizard.action_compute()

        lines = wizard.planning_line_ids.sorted("date")
        self.assertEqual(len(lines), 4)
        # Monday absent (day off in odd week).
        # Tuesday and Wednesday: full leave days.
        self.assertEqual(lines[0].date, date(2026, 5, 19))
        self.assertAlmostEqual(lines[0].hours_work, 0.0)
        self.assertAlmostEqual(lines[0].hours_leave, 8.0)
        self.assertAlmostEqual(lines[0].hours_holiday, 0.0)
        self.assertEqual(lines[1].date, date(2026, 5, 20))
        self.assertAlmostEqual(lines[1].hours_work, 0.0)
        self.assertAlmostEqual(lines[1].hours_leave, 8.0)
        self.assertAlmostEqual(lines[1].hours_holiday, 0.0)
        # Thursday and Friday: full work days.
        self.assertEqual(lines[2].date, date(2026, 5, 21))
        self.assertAlmostEqual(lines[2].hours_work, 8.0)
        self.assertAlmostEqual(lines[2].hours_leave, 0.0)
        self.assertAlmostEqual(lines[2].hours_holiday, 0.0)
        self.assertEqual(lines[3].date, date(2026, 5, 22))
        self.assertAlmostEqual(lines[3].hours_work, 8.0)
        self.assertAlmostEqual(lines[3].hours_leave, 0.0)
        self.assertAlmostEqual(lines[3].hours_holiday, 0.0)

    def test_five_day_week_with_holiday_splitting_leave(self):
        """Mon-Fri week: leave Tue–Thu with holiday on Wed → 5 lines."""
        self._make_public_holiday(date(2026, 5, 27))
        self._make_validated_leave(
            self.employee,
            datetime(2026, 5, 26, 9, 0, 0),
            datetime(2026, 5, 28, 17, 0, 0),
        )
        wizard = self._create_wizard(
            self.employee, date(2026, 5, 25), date(2026, 5, 29)
        )
        wizard.action_compute()

        lines = wizard.planning_line_ids.sorted("date")
        self.assertEqual(len(lines), 5)
        # Monday: work.
        self.assertEqual(lines[0].date, date(2026, 5, 25))
        self.assertAlmostEqual(lines[0].hours_work, 8.0)
        self.assertAlmostEqual(lines[0].hours_leave, 0.0)
        self.assertAlmostEqual(lines[0].hours_holiday, 0.0)
        # Tuesday: leave.
        self.assertEqual(lines[1].date, date(2026, 5, 26))
        self.assertAlmostEqual(lines[1].hours_work, 0.0)
        self.assertAlmostEqual(lines[1].hours_leave, 8.0)
        self.assertAlmostEqual(lines[1].hours_holiday, 0.0)
        # Wednesday: public holiday.
        self.assertEqual(lines[2].date, date(2026, 5, 27))
        self.assertAlmostEqual(lines[2].hours_work, 0.0)
        self.assertAlmostEqual(lines[2].hours_leave, 0.0)
        self.assertAlmostEqual(lines[2].hours_holiday, 8.0)
        # Thursday: leave.
        self.assertEqual(lines[3].date, date(2026, 5, 28))
        self.assertAlmostEqual(lines[3].hours_work, 0.0)
        self.assertAlmostEqual(lines[3].hours_leave, 8.0)
        self.assertAlmostEqual(lines[3].hours_holiday, 0.0)
        # Friday: work.
        self.assertEqual(lines[4].date, date(2026, 5, 29))
        self.assertAlmostEqual(lines[4].hours_work, 8.0)
        self.assertAlmostEqual(lines[4].hours_leave, 0.0)
        self.assertAlmostEqual(lines[4].hours_holiday, 0.0)

    def test_four_day_week_with_holiday_and_partial_leave(self):
        """Odd week (Mon off): holiday Thu, 4h leave Fri → 4 lines."""
        self._make_public_holiday(date(2026, 5, 21))
        self._make_validated_leave(
            self.employee_two_week,
            datetime(2026, 5, 22, 9, 0, 0),
            datetime(2026, 5, 22, 13, 0, 0),
            full_day=False,
        )
        wizard = self._create_wizard(
            self.employee_two_week, date(2026, 5, 18), date(2026, 5, 22)
        )
        wizard.action_compute()

        lines = wizard.planning_line_ids.sorted("date")
        self.assertEqual(len(lines), 4)
        # Monday absent (day off in odd week).
        # Tuesday and Wednesday: full work days.
        self.assertEqual(lines[0].date, date(2026, 5, 19))
        self.assertAlmostEqual(lines[0].hours_work, 8.0)
        self.assertAlmostEqual(lines[0].hours_leave, 0.0)
        self.assertAlmostEqual(lines[0].hours_holiday, 0.0)
        self.assertEqual(lines[1].date, date(2026, 5, 20))
        self.assertAlmostEqual(lines[1].hours_work, 8.0)
        self.assertAlmostEqual(lines[1].hours_leave, 0.0)
        self.assertAlmostEqual(lines[1].hours_holiday, 0.0)
        # Thursday: public holiday replaces the work slot.
        self.assertEqual(lines[2].date, date(2026, 5, 21))
        self.assertAlmostEqual(lines[2].hours_work, 0.0)
        self.assertAlmostEqual(lines[2].hours_leave, 0.0)
        self.assertAlmostEqual(lines[2].hours_holiday, 8.0)
        # Friday: 4h leave followed by 4h work.
        self.assertEqual(lines[3].date, date(2026, 5, 22))
        self.assertAlmostEqual(lines[3].hours_work, 4.0)
        self.assertAlmostEqual(lines[3].hours_leave, 4.0)
        self.assertAlmostEqual(lines[3].hours_holiday, 0.0)

    def test_timezone_mismatch_logs_warning(self):
        """A warning is logged when the employee's user timezone differs from the calendar."""
        user = self.env["res.users"].create(
            {
                "name": "TZ Mismatch User",
                "login": "tz_mismatch_user@example.com",
                "tz": "Europe/Amsterdam",
            }
        )
        self.employee.write({"user_id": user.id})
        logger_name = "odoo.addons.hr_holidays_work_and_leaves.models.hr_employee"
        with self.assertLogs(logger_name, level="WARNING"):
            self.employee._get_work_hours_and_leaves(
                datetime(2026, 5, 25, 7, 0, 0),
                datetime(2026, 5, 29, 18, 0, 0),
            )
