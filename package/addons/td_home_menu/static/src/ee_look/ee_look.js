import { session } from "@web/session";
import { registerTemplateExtension } from "@web/core/templates";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

/**
 * Owner remark 2026-11-16 (A-17 №17): a light navbar with the icon and the name of the application on the left and
 * forms / lists in the spirit of Odoo 19 Enterprise — own styles only (ee_look.scss), no code or assets of Enterprise.
 * Switch: system parameter td_home_menu.ee_look (session_info td_ee_look), on by default; Community only.
 */
export function isTdEeLook() {
    return Boolean(session.td_ee_look);
}

const NAVBAR_ICON = `
<t t-inherit="web.NavBar" t-inherit-mode="extension">
    <xpath expr="//t[@t-call='web.NavBar.AppsMenu']" position="after">
        <img t-if="tdEeLook and !this.ui.isSmall and currentApp and currentApp.webIconData" class="td_app_icon"
             t-att-src="currentApp.webIconData" alt=""/>
    </xpath>
</t>`;

if (isTdEeLook()) {
    document.documentElement.classList.add("td_ee_look");
    registerTemplateExtension("web.NavBar", "/td_home_menu/static/src/ee_look/ee_look.js", NAVBAR_ICON);
    patch(NavBar.prototype, {
        get tdEeLook() {
            return true;
        },
    });
}
