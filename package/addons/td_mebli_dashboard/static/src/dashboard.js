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

    async openMargin(card) {
        // drill-down shows exactly the orders counted as «low margin» on the card, so the totals agree
        if (card.low_ids && card.low_ids.length) {
            const ref = await this.orm.call("ir.model.data", "check_object_reference", ["td_mebli_sale", "sale_order_td_low_margin_list"]);
            this.actionService.doAction({
                type: "ir.actions.act_window", name: card.alert, res_model: "sale.order",
                views: [[ref[1], "list"], [false, "form"]], domain: [["id", "in", card.low_ids]],
            });
        } else {
            this.open(card.action);
        }
    }

    open(xmlid) {
        if (xmlid) {
            this.actionService.doAction(xmlid);
        }
    }
}

registry.category("actions").add("td_mebli_dashboard", TdMebliDashboard);
