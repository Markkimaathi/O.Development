/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { RockerCalendarController } from './calendar_controller';
//import { RockerCalendarModel } from './calendar_model';
//import { RockerCalendarRenderer} from './calendar_renderer';

export const RockerCalendarView = {
    ...calendarView,
    Controller: RockerCalendarController,
//    Model: RockerCalendarModel,
//    Renderer: RockerCalendarRenderer,
};

registry.category("views").add("rocker_calendar", RockerCalendarView);

