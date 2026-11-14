import { Component, markup, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";

const MODEL = "td.knowledge.article";

/**
 * Knowledge base reader: tree of sections on the left, search, the article on the right.
 * Client action «td_knowledge.reader» (record action_td_knowledge_reader, path td-knowledge);
 * params.article_id opens an article (from the «Help» icon).
 */
export class TdKnowledgeReader extends Component {
    static template = "td_knowledge.Reader";
    static props = ["*"];
    static displayName = _t("Knowledge Base");

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ui = useService("ui");
        this.state = useState({
            query: "",
            articles: [],
            isEditor: false,
            article: null,
            collapsed: {},
            showTree: true,
        });
        this.search = debounce(() => this.loadTree(), 250);
        onWillStart(async () => {
            await this.loadTree();
            const params = this.props.action?.params || {};
            const first = this.state.articles.find((a) => !a.parent_id);
            const articleId = params.article_id || first?.id;
            if (articleId) {
                await this.open(articleId);
            }
        });
    }

    async loadTree() {
        const data = await this.orm.call(MODEL, "td_reader_tree", [this.state.query]);
        this.state.articles = data.articles;
        this.state.isEditor = data.is_editor;
    }

    get roots() {
        return this.childrenOf(false);
    }

    childrenOf(parentId) {
        return this.state.articles.filter((a) => a.parent_id === parentId);
    }

    hasChildren(article) {
        return this.state.articles.some((a) => a.parent_id === article.id);
    }

    toggle(article) {
        this.state.collapsed[article.id] = !this.state.collapsed[article.id];
    }

    async open(articleId) {
        const article = await this.orm.call(MODEL, "td_reader_article", [articleId]);
        if (article) {
            article.body = markup(article.body);
            this.state.article = article;
            if (this.ui.isSmall) {
                this.state.showTree = false;
            }
        }
    }

    onSearch(ev) {
        this.state.query = ev.target.value;
        this.search();
    }

    edit() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: MODEL,
            res_id: this.state.article.id,
            views: [[false, "form"]],
        });
    }

    create(parentId = false) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: MODEL,
            views: [[false, "form"]],
            context: { default_parent_id: parentId },
        });
    }
}

registry.category("actions").add("td_knowledge.reader", TdKnowledgeReader);
