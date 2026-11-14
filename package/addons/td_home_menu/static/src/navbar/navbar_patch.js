import { registerTemplateExtension } from "@web/core/templates";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";
import { isTdHomeMenuActive, TD_HOME_MENU_ACTION } from "./home_menu_service";

/**
 * Extension of web.NavBar.AppsMenu (web/static/src/webclient/navbar/navbar.xml). It is registered from JS and only on
 * Community: with web_enterprise installed the navbar template is not touched at all (no xpath can fail on a template
 * changed by Enterprise). registerTemplateExtension is what Odoo itself generates for every XML extension
 * (odoo/addons/base/models/assetsbundle.py generate_xml_bundle).
 */
const NAVBAR_EXTENSION = `
<t t-inherit="web.NavBar.AppsMenu" t-inherit-mode="extension">
    <xpath expr="//div[hasclass('o_navbar_apps_menu')]" position="before">
        <div t-if="!isScopedApp" class="o_navbar_apps_menu td_home_menu_toggle">
            <button class="dropdown-toggle" data-hotkey="h" t-att-title="tdHomeMenuTitle"
                    t-att-aria-label="tdHomeMenuTitle" t-on-click="onTdHomeMenuClick">
                <i class="oi oi-apps"/>
            </button>
        </div>
    </xpath>
    <xpath expr="//div[hasclass('o_navbar_apps_menu')][not(hasclass('td_home_menu_toggle'))]" position="attributes">
        <attribute name="t-if">false</attribute>
    </xpath>
    <xpath expr="//div[hasclass('mx-2')]" position="attributes">
        <attribute name="t-else"/>
        <attribute name="t-elif">isScopedApp</attribute>
    </xpath>
    <xpath expr="//a[hasclass('o_menu_toggle')]" position="before">
        <button class="td_home_menu_toggle_mobile border-0 px-3 h-100" t-att-title="tdHomeMenuTitle"
                t-att-aria-label="tdHomeMenuTitle" t-on-click="onTdHomeMenuClick">
            <i class="oi oi-apps fs-4"/>
        </button>
    </xpath>
</t>`;

if (isTdHomeMenuActive()) {
    registerTemplateExtension("web.NavBar.AppsMenu", "/td_home_menu/static/src/navbar/navbar_patch.js", NAVBAR_EXTENSION);

    patch(NavBar.prototype, {
        get tdHomeMenuTitle() {
            return _t("Home screen");
        },
        async onTdHomeMenuClick() {
            await this.actionService.doAction(TD_HOME_MENU_ACTION, { clearBreadcrumbs: true });
        },
    });

    patch(WebClient.prototype, {
        /** After the login (no action in the URL) open the home screen instead of the first application. */
        _loadDefaultApp() {
            return this.actionService.doAction(TD_HOME_MENU_ACTION, { clearBreadcrumbs: true });
        },
    });
}
