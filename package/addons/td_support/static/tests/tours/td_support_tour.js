import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("td_support_tour", {
    url: "/odoo/action-base.action_res_users",
    steps: () => [
        { trigger: ".o_main_navbar .td_support_systray button", run: "click" },
        { trigger: ".td_support_dialog .td_support_subject", run: "edit Tour: cannot print the order" },
        { trigger: ".td_support_dialog .td_support_description", run: "edit The print button does nothing." },
        // the user sees what will be sent before the consent
        { trigger: ".td_support_preview button", run: "click" },
        { trigger: ".td_support_preview td:contains(19.0)" },
        { trigger: ".td_support_dialog .td_support_send[disabled]" },
        { trigger: ".td_support_dialog .td_support_consent", run: "check" },
        { trigger: ".td_support_dialog .td_support_send:not([disabled])", run: "click" },
        { trigger: ".o_notification:contains(TDS/)" },
    ],
});
