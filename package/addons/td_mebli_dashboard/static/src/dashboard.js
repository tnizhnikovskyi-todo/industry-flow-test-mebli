import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TdMebliDashboard extends Component {
    static template = "td_mebli_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({ data: null });
        onWillStart(async () => {
            this.state.data = await this.orm.call("td.mebli.dashboard", "get_data", []);
        });
    }

    open(xmlid) {
        if (xmlid) {
            this.actionService.doAction(xmlid);
        }
    }
}

registry.category("actions").add("td_mebli_dashboard", TdMebliDashboard);
