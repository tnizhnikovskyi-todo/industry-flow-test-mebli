import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { TdSupportDialog } from "../support_dialog/support_dialog";

export class TdSupportSystray extends Component {
    static template = "td_support.Systray";
    static props = {};

    setup() {
        this.dialog = useService("dialog");
    }

    open() {
        this.dialog.add(TdSupportDialog, {});
    }
}

// web/static/src/webclient/navbar/navbar.js: the navbar renders every entry of the «systray» registry
registry.category("systray").add("td_support.Systray", { Component: TdSupportSystray }, { sequence: 25 });
