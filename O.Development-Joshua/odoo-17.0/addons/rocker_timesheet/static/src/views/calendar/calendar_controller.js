/** @odoo-module **/

//import { _t } from "@web/core/l10n/translation";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { useService } from "@web/core/utils/hooks";
export class RockerCalendarController extends CalendarController {
    setup() {
        console.log('setup');
        super.setup();
        this.actionService = useService("action");
    }
    async all() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_all_tasks", {});}
    async member() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_member_tasks", {});}
    async billable() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_billable_tasks", {});}
    async nonbillable() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_nonbillable_tasks", {});}
    async internal() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_internal_tasks", {});}
    async mine() {await this.actionService.doAction("rocker_timesheet.action_searchpanel_mine_tasks", {});}
//        $(document).find('.o_list_button_add').click();
}

RockerCalendarController.template = "rocker_timesheet.RockerCalendarController";
RockerCalendarController.components = {
    ...RockerCalendarController.components,
//    QuickCreateFormView: CalendarQuickCreate,
}

