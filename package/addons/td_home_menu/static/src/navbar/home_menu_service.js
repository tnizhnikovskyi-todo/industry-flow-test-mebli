import { session } from "@web/session";

/** True on Community; False when web_enterprise is installed (models/ir_http.py session_info). */
export function isTdHomeMenuActive() {
    return Boolean(session.td_home_menu_active);
}

export const TD_HOME_MENU_ACTION = {
    type: "ir.actions.client",
    tag: "td_home_menu",
};
