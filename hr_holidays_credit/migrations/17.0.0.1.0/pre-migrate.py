# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade

_rename_fields = [
    (
        "hr.leave.type",
        "hr_leave_type",
        "allow_credit",
        "allows_negative",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    for model, table, oldfield, newfield in _rename_fields:
        if not openupgrade.column_exists(
            env.cr, table, oldfield
        ) or openupgrade.column_exists(env.cr, table, newfield):
            continue
        openupgrade.rename_fields(env, [(model, table, oldfield, newfield)])
