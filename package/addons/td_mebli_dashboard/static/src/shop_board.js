import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Position 39 (F-65): the shop floor board on a TV — refreshes itself every minute, read only
export class TdMebliShopBoard extends Component {
    static template = "td_mebli_dashboard.ShopBoard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({ data: null });
        onWillStart(() => this.load());
        onMounted(() => { this.timer = setInterval(() => this.load(), 60000); });
        onWillUnmount(() => clearInterval(this.timer));
    }

    async load() {
        this.state.data = await this.orm.call("td.mebli.dashboard", "get_shop_board", []);
    }
}

registry.category("actions").add("td_mebli_shop_board", TdMebliShopBoard);
