# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields


def post_init_hook(env):
    """Backfill future public-holiday timesheets for existing employees."""
    holiday_lines = env["calendar.public.holiday.line"].search(
        [("date", ">=", fields.Date.today())]
    )
    if not holiday_lines:
        return

    employees = env["hr.employee"].search(
        [
            ("active", "=", True),
            ("address_id", "!=", False),
        ]
    )
    if not employees:
        return

    holiday_lines._generate_public_holiday_timesheets(employees)
