import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { fuzzyLookup } from "@web/core/utils/search";

// class of <body> while the home screen is shown: the navbar hides the application menu and the brand (navbar.scss)
export const HOME_MODE_CLASS = "td_home_menu_mode";

/**
 * ToDo home screen (Community only): tiles of the root menus with their web_icon, search by name, keyboard.
 * Written from scratch (no code or resources of web_enterprise): the navbar shows only the systray, the search field
 * is always at the top, one tile is highlighted (under the mouse or chosen with the arrows).
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
        // focused: index of the highlighted tile, -1 — none
        this.state = useState({ query: "", focused: -1 });
        this.inputRef = useRef("input");
        this.gridRef = useRef("grid");
        onMounted(() => {
            document.body.classList.add(HOME_MODE_CLASS);
            // no on-screen keyboard on a phone until the user taps the search
            if (!this.ui.isSmall) {
                this.inputRef.el?.focus();
            }
        });
        onWillUnmount(() => document.body.classList.remove(HOME_MODE_CLASS));
    }

    get apps() {
        const apps = this.menuService.getApps().filter((app) => app.actionID);
        const query = this.state.query.trim();
        return query ? fuzzyLookup(query, apps, (app) => app.name) : apps;
    }

    iconStyle(app) {
        const [, color] = (app.webIcon || "").split(",");
        return `color: ${color || "#714B67"};`;
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
        this.state.focused = this.state.query.trim() ? 0 : -1;
    }

    onTileEnter(index) {
        this.state.focused = index;
    }

    onTileLeave(index) {
        if (this.state.focused === index) {
            this.state.focused = -1;
        }
    }

    /** Arrows move the highlighted tile, Enter opens it (or the first match of the search), Esc clears the search. */
    onKeydown(ev) {
        const count = this.apps.length;
        const moves = {
            ArrowRight: 1,
            ArrowLeft: -1,
            ArrowDown: this.columns,
            ArrowUp: -this.columns,
        };
        if (ev.key in moves) {
            if (!count) {
                return;
            }
            ev.preventDefault();
            const next = this.state.focused < 0 ? 0 : this.state.focused + moves[ev.key];
            this.state.focused = Math.min(Math.max(next, 0), count - 1);
        } else if (ev.key === "Enter") {
            const app = this.apps[this.state.focused] || (this.state.query.trim() && this.apps[0]);
            if (app) {
                ev.preventDefault();
                this.openApp(app);
            }
        } else if (ev.key === "Escape") {
            this.state.query = "";
            this.state.focused = -1;
        }
    }

    async openApp(app) {
        if (app) {
            await this.menuService.selectMenu(app);
        }
    }
}

registry.category("actions").add("td_home_menu", TdHomeMenu);
