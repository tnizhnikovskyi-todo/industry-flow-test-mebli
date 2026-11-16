import { registry } from "@web/core/registry";

function check(condition, message) {
    if (!condition) {
        throw new Error(`td_home_menu_tour: ${message}`);
    }
}

registry.category("web_tour.tours").add("td_home_menu_tour", {
    url: "/odoo",
    steps: () => [
        // after the login (no action in the URL) the home screen opens
        { trigger: ".td_home_menu .td_home_menu_app" },
        { trigger: ".td_home_menu_app[data-menu-xmlid='base.menu_administration']" },
        {
            // the navbar of the home screen: only the systray, no menu of the application and no brand
            trigger: "body.td_home_menu_mode .o_main_navbar .o_menu_systray",
            run() {
                for (const selector of [".o_menu_brand", ".o_menu_sections", ".o_navbar_apps_menu"]) {
                    const el = document.querySelector(`.o_main_navbar ${selector}`);
                    check(!el || el.offsetParent === null, `${selector} is shown on the home screen`);
                }
            },
        },
        {
            // the search field is always at the top; 6 columns on a desktop; tiles of the same size;
            // one-line captions with an ellipsis and the full name in the title
            trigger: ".td_home_menu_search .td_home_menu_input",
            run() {
                const grid = document.querySelector(".td_home_menu_grid");
                const columns = getComputedStyle(grid).gridTemplateColumns.split(" ").length;
                if (window.innerWidth >= 992) {
                    check(columns === 6, `${columns} columns at ${window.innerWidth} px, expected 6`);
                }
                const sizes = new Set([...document.querySelectorAll(".td_home_menu_tile")].map(
                    (tile) => `${tile.offsetWidth}x${tile.offsetHeight}`));
                check(sizes.size === 1, `tiles of different sizes: ${[...sizes].join(", ")}`);
                for (const app of document.querySelectorAll(".td_home_menu_app")) {
                    const caption = app.querySelector(".td_home_menu_caption");
                    const style = getComputedStyle(caption);
                    check(style.textOverflow === "ellipsis" && style.whiteSpace === "nowrap",
                        `caption «${caption.textContent}» is not one line with an ellipsis`);
                    check(app.title === caption.textContent.trim(), `no full name in the title of «${app.title}»`);
                }
            },
        },
        // no tile is highlighted until the mouse or the arrows choose one
        { trigger: ".td_home_menu_grid:not(:has(.td_focused))" },
        { trigger: ".td_home_menu_app:nth-child(2)", run: "hover" },
        { trigger: ".td_home_menu_app.td_focused:nth-child(2)" },
        { trigger: ".td_home_menu_input", run: "press ArrowRight" },
        {
            trigger: ".td_home_menu_app.td_focused:nth-child(3)",
            run() {
                check(document.querySelectorAll(".td_home_menu_app.td_focused").length === 1,
                    "more than one highlighted tile");
            },
        },
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
        // Esc clears the search: all tiles come back
        { trigger: ".td_home_menu_input", run: "press Escape" },
        { trigger: ".td_home_menu_grid:has(.td_home_menu_app:nth-child(2))" },
        {
            trigger: ".td_home_menu_input",
            async run(helpers) {
                const caption = document.querySelector(
                    ".td_home_menu_app[data-menu-xmlid='base.menu_administration'] .td_home_menu_caption"
                );
                await helpers.edit(caption.textContent.trim());
            },
        },
        { trigger: ".td_home_menu_app.td_focused[data-menu-xmlid='base.menu_administration']" },
        { trigger: ".td_home_menu_input", run: "press Enter" },
        { trigger: ".o_action:not(.td_home_menu)" },
        // the application has its navbar again; its button brings the home screen back
        { trigger: "body:not(.td_home_menu_mode) .o_main_navbar .o_menu_brand" },
        { trigger: ".o_main_navbar .td_home_menu_toggle button", run: "click" },
        { trigger: ".td_home_menu .td_home_menu_app" },
    ],
});
