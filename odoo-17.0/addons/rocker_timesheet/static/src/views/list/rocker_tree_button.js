/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class RockerListController extends ListController {
    setup() {
        super.setup();
    }
    async OnRollerClick() {
        var self = this;
        await this.actionService.doAction("rocker_timesheet.action_create_rolling", {
            on_close: function () {
                console.log('OnRollerClick close');
            }
        });
        $(document).find('.o_list_button_add').click();
    }
}
registry.category("views").add("rocker_list", {
    ...listView,
    Controller: RockerListController,
    buttonTemplate: "rocker_timesheet.list_buttons",
});
