# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade

# Large number to simulate previous behavior of unlimited negative balance
UNLIMITED_NEGATIVE = 100


@openupgrade.migrate()
def migrate(env, version):
    # In leave types with negative allowed, set the max allowed negative to
    # UNLIMITED_NEGATIVE, a large number to simulate previous behavior of
    # unlimited negative balance
    openupgrade.logged_query(
        env.cr,
        f"""
        UPDATE hr_leave_type
        SET max_allowed_negative = {UNLIMITED_NEGATIVE}
        WHERE allows_negative = TRUE
            AND (max_allowed_negative IS NULL
                OR max_allowed_negative < {UNLIMITED_NEGATIVE})
        """,
    )
