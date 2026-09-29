# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    # The OCA "Exclude Public Holidays" flag is replaced by the standard
    # "Ignore Public Holidays" setting, which means the opposite. The column
    # of the standard field exists already: hr_holidays is upgraded first.
    if not _column_exists(cr, "hr_leave_type", "exclude_public_holidays"):
        return
    if not _column_exists(cr, "hr_leave_type", "include_public_holidays_in_duration"):
        return
    cr.execute(
        """
        UPDATE hr_leave_type
        SET include_public_holidays_in_duration =
            NOT COALESCE(exclude_public_holidays, TRUE)
        """
    )
