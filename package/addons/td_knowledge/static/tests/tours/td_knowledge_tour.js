import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("td_knowledge_tour", {
    url: "/odoo/action-base.action_res_users",
    steps: () => [
        { trigger: ".o_list_view .o_data_row" },
        // the help icon shows the article linked to the users screen (created by the test)
        { trigger: ".td_knowledge_systray .td_knowledge_count:contains(1)" },
        { trigger: ".td_knowledge_systray button", run: "click" },
        { trigger: ".td_knowledge_help_item:contains(Tour: users)", run: "click" },
        // the reader opens the article
        { trigger: ".td_knowledge_title:contains(Tour: users)" },
        { trigger: ".td_knowledge_body:contains(How to invite a user)" },
        // search in the text of the articles
        { trigger: ".td_knowledge_search", run: "edit invite" },
        { trigger: ".td_knowledge_link:contains(Tour: users)" },
        { trigger: ".td_knowledge_edit" },
    ],
});
