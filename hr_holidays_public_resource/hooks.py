# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Generate the personal entries of the regional public holidays.

    ``calendar_public_holiday_resource`` synchronised everything it could
    when it was installed, but resolving a regional public holiday to the
    people of its regions needs this module, so the synchronisation runs
    once more with it loaded.
    """
    env["calendar.public.holiday.line"]._get_lines_to_sync()._sync_global_leaves()
