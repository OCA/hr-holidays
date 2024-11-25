from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # convert date_start and date_end columns
    # to be date and not timestamp
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE hr_leave_type
        ALTER COLUMN date_start
        TYPE DATE
        USING date_start::DATE
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE hr_leave_type
        ALTER COLUMN date_end
        TYPE DATE
        USING date_end::DATE
        """,
    )
