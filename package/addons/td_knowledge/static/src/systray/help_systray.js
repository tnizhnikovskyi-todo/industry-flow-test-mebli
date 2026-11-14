import { Component, onWillStart, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";

const MODEL = "td.knowledge.article";

/** Model and application of the screen the user is on (action service + menu service). */
function currentScreen(env) {
    const controller = env.services.action.currentController;
    const model = controller?.props?.resModel || controller?.action?.res_model || false;
    const app = env.services.menu.getCurrentApp();
    return { model, menuId: app?.id || false };
}

export class TdKnowledgeHelpDialog extends Component {
    static template = "td_knowledge.HelpDialog";
    static components = { Dialog };
    static props = { close: Function, model: [String, Boolean], menuId: [Number, Boolean] };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ articles: [], modelId: false, modelName: "", isEditor: false });
        onWillStart(async () => {
            const data = await this.orm.call(MODEL, "td_screen_help", [this.props.model, this.props.menuId]);
            Object.assign(this.state, {
                articles: data.articles,
                modelId: data.model_id,
                modelName: data.model_name,
                isEditor: data.is_editor,
            });
        });
    }

    get title() {
        return _t("Help for this screen");
    }

    openArticle(article) {
        this.props.close();
        this.action.doAction({
            type: "ir.actions.client",
            tag: "td_knowledge.reader",
            params: { article_id: article.id },
        });
    }

    openAll() {
        this.props.close();
        this.action.doAction("td_knowledge.action_td_knowledge_reader");
    }

    addArticle() {
        this.props.close();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: MODEL,
            views: [[false, "form"]],
            context: {
                default_model_ids: this.state.modelId ? [this.state.modelId] : [],
                default_menu_ids: !this.state.modelId && this.props.menuId ? [this.props.menuId] : [],
            },
        });
    }
}

export class TdKnowledgeSystray extends Component {
    static template = "td_knowledge.Systray";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({ count: 0 });
        this.lastKey = null;
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.refresh());
        onWillStart(() => this.refresh());
    }

    async refresh() {
        const { model, menuId } = currentScreen(this.env);
        const key = `${model}|${menuId}`;
        if (key === this.lastKey) {
            return;
        }
        this.lastKey = key;
        this.state.count = model || menuId ? await this.orm.silent.call(MODEL, "td_screen_count", [model, menuId]) : 0;
    }

    open() {
        const { model, menuId } = currentScreen(this.env);
        this.dialog.add(TdKnowledgeHelpDialog, { model, menuId });
    }
}

// web/static/src/webclient/navbar/navbar.js: the navbar renders every entry of the «systray» registry
registry.category("systray").add("td_knowledge.Systray", { Component: TdKnowledgeSystray }, { sequence: 26 });
