import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

/**
 * The standard Public Holidays list shows records generated from the public
 * holiday calendar. Without a word of explanation the read-only rows and the
 * missing New button look like a bug, so the list says where they come from.
 */
export class PublicHolidayListController extends ListController {}

PublicHolidayListController.template =
    "hr_holidays_public_resource.PublicHolidayListView";

registry.category("views").add("public_holiday_list", {
    ...listView,
    Controller: PublicHolidayListController,
});
