import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { fuzzyLookup } from "@web/core/utils/search";

/**
 * ToDo home screen (Community only): tiles of the root menus with their web_icon, search by name, keyboard.
 * Client action «td_home_menu»: the action service puts its tag in the URL and reopens it from the registry
 * (web/static/src/webclient/actions/action_service.js, see README).
 */
export class TdHomeMenu extends Component {
    static template = "td_home_menu.HomeMenu";
    static props = ["*"];
    static displayName = _t("Applications");

    setup() {
        this.menuService = useService("menu");
        this.ui = useService("ui");
        this.state = useState({ query: "", focused: 0 });
        this.inputRef = useRef("input");
        this.gridRef = useRef("grid");
        onMounted(() => {
            // no on-screen keyboard on a phone until the user taps the search
            if (!this.ui.isSmall) {
                this.inputRef.el?.focus();
            }
        });
    }

    get apps() {
        const apps = this.menuService.getApps().filter((app) => app.actionID);
        const query = this.state.query.trim();
        return query ? fuzzyLookup(query, apps, (app) => app.name) : apps;
    }

    iconStyle(app) {
        if (app.webIconData) {
            return "";
        }
        const [, color, background] = (app.webIcon || "").split(",");
        return `color: ${color || "#ffffff"}; background-color: ${background || "#714B67"};`;
    }

    iconClass(app) {
        const [iconClass] = (app.webIcon || "").split(",");
        return iconClass || "fa fa-cube";
    }

    get columns() {
        const tiles = this.gridRef.el ? [...this.gridRef.el.querySelectorAll(".td_home_menu_app")] : [];
        if (!tiles.length) {
            return 1;
        }
        const top = tiles[0].offsetTop;
        return tiles.filter((tile) => tile.offsetTop === top).length || 1;
    }

    onInput(ev) {
        this.state.query = ev.target.value;
        this.state.focused = 0;
    }

    onKeydown(ev) {
        const count = this.apps.length;
        if (!count && ev.key !== "Escape") {
            return;
        }
        const moves = {
            ArrowRight: 1,
            ArrowLeft: -1,
            ArrowDown: this.columns,
            ArrowUp: -this.columns,
        };
        if (ev.key in moves) {
            ev.preventDefault();
            const next = this.state.focused + moves[ev.key];
            this.state.focused = Math.min(Math.max(next, 0), count - 1);
        } else if (ev.key === "Enter") {
            ev.preventDefault();
            this.openApp(this.apps[this.state.focused] || this.apps[0]);
        } else if (ev.key === "Escape") {
            this.state.query = "";
            this.state.focused = 0;
        }
    }

    async openApp(app) {
        if (app) {
            await this.menuService.selectMenu(app);
        }
    }
}

registry.category("actions").add("td_home_menu", TdHomeMenu);
