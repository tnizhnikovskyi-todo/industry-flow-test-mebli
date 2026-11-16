import { registry } from "@web/core/registry";

const KEY = "td_home_menu.chatter_width";

function check(condition, message) {
    if (!condition) {
        throw new Error(`td_chatter_resize_tour: ${message}`);
    }
}

function drag(handle, dx) {
    const box = handle.getBoundingClientRect();
    const x = box.left + box.width / 2;
    const y = box.top + 50;
    const opts = (cx) => ({ bubbles: true, cancelable: true, clientX: cx, clientY: y, pointerId: 1, button: 0 });
    handle.dispatchEvent(new PointerEvent("pointerdown", opts(x)));
    document.dispatchEvent(new PointerEvent("pointermove", opts(x + dx)));
    document.dispatchEvent(new PointerEvent("pointerup", opts(x + dx)));
}

// A-17 №17: the handle between the form and the chatter changes the width; the width stays after a reload;
// a double click resets it
registry.category("web_tour.tours").add("td_chatter_resize_tour", {
    steps: () => [
        {
            trigger: ".o_main_navbar .td_app_icon",
        },
        {
            trigger: ".o-mail-Form-chatter.o-aside > .td_chatter_handle",
            run() {
                window.localStorage.removeItem(KEY);
                const chatter = document.querySelector(".o-mail-Form-chatter.o-aside");
                const before = chatter.getBoundingClientRect().width;
                drag(this.anchor, -150);
                const after = chatter.getBoundingClientRect().width;
                check(after > before + 100, `the chatter is not wider after dragging: ${before} -> ${after}`);
                const stored = parseInt(window.localStorage.getItem(KEY), 10);
                check(Math.abs(stored - after) <= 2, `stored width ${stored} != ${after}`);
                window.location.reload();
            },
            expectUnloadPage: true,
        },
        {
            trigger: ".o-mail-Form-chatter.o-aside > .td_chatter_handle",
            run() {
                const chatter = document.querySelector(".o-mail-Form-chatter.o-aside");
                const stored = parseInt(window.localStorage.getItem(KEY), 10);
                const width = chatter.getBoundingClientRect().width;
                check(Math.abs(stored - width) <= 2, `after the reload the width ${width} != stored ${stored}`);
                this.anchor.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                check(window.localStorage.getItem(KEY) === null, "a double click does not reset the width");
            },
        },
    ],
});
