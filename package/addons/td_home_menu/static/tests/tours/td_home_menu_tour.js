import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("td_home_menu_tour", {
    url: "/odoo",
    steps: () => [
        // after the login (no action in the URL) the home screen opens
        { trigger: ".td_home_menu .td_home_menu_app" },
        // the language of the page for the line breaks of the captions (A-11-fix4)
        { trigger: "html[lang]:not([lang=''])" },
        { trigger: ".td_home_menu_app[data-menu-xmlid='base.menu_administration']" },
        // search an application by name, then open it with the keyboard
        {
            // the name of the Settings tile in the language of the user
            trigger: ".td_home_menu_input",
            async run(helpers) {
                const caption = document.querySelector(
                    ".td_home_menu_app[data-menu-xmlid='base.menu_administration'] .td_home_menu_caption"
                );
                await helpers.edit(caption.textContent.trim());
            },
        },
        { trigger: ".td_home_menu_grid:not(:has(.td_home_menu_app:nth-child(2)))" },
        { trigger: ".td_home_menu_app.td_focused[data-menu-xmlid='base.menu_administration']" },
        { trigger: ".td_home_menu_input", run: "press Enter" },
        { trigger: ".o_action:not(.td_home_menu)" },
        // the navbar button brings the home screen back
        { trigger: ".o_main_navbar .td_home_menu_toggle button", run: "click" },
        { trigger: ".td_home_menu .td_home_menu_app" },
    ],
});
