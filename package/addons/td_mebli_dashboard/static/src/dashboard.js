import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";

export class TdMebliDashboard extends Component {
    static template = "td_mebli_dashboard.Dashboard";
    static props = ["*"];
    static components = { Layout };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({ data: null });
        onWillStart(async () => {
            this.state.data = await this.orm.call("td.mebli.dashboard", "get_data", []);
        });
    }

    // a card opens exactly the records it counted, so the totals of the report equal the card
    open(card) {
        const drill = card.drill;
        if (!drill) {
            return;
        }
        this.actionService.doAction({
            type: "ir.actions.act_window", name: drill.name, res_model: drill.res_model,
            views: drill.views, domain: [["id", "in", drill.ids]], context: { create: false },
        });
    }
}

registry.category("actions").add("td_mebli_dashboard", TdMebliDashboard);
