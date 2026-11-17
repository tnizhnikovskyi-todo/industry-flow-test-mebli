import { onMounted, onPatched, useRef } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { isTdEeLook } from "../ee_look/ee_look";

/**
 * Owner remark 2026-11-16 (A-17 №17): the width of the chatter beside the form is changed by dragging the handle
 * between the form and the chatter; the width is remembered per user and browser (localStorage
 * td_home_menu.chatter_width), a double click resets it. Only when the chatter is beside the form (mail «o-aside»,
 * wide screens); under the form (narrow screens) there is no handle.
 */
export const TD_CHATTER_KEY = "td_home_menu.chatter_width";
export const TD_CHATTER_MIN = 320;
export const TD_CHATTER_MAX_RATIO = 0.6;

function readWidth() {
    try {
        const value = parseInt(browser.localStorage.getItem(TD_CHATTER_KEY), 10);
        return Number.isFinite(value) && value > 0 ? value : null;
    } catch {
        return null;
    }
}

function writeWidth(value) {
    try {
        if (value) {
            browser.localStorage.setItem(TD_CHATTER_KEY, String(value));
        } else {
            browser.localStorage.removeItem(TD_CHATTER_KEY);
        }
    } catch {
        // private window or blocked storage: the width is kept for this page only
    }
}

export function clampChatterWidth(width, total) {
    const max = Math.max(TD_CHATTER_MIN, Math.round(total * TD_CHATTER_MAX_RATIO));
    return Math.min(Math.max(Math.round(width), TD_CHATTER_MIN), max);
}

function applyWidth(chatter, width) {
    if (width) {
        const total = chatter.parentElement ? chatter.parentElement.getBoundingClientRect().width : window.innerWidth;
        const value = clampChatterWidth(width, total);
        chatter.style.setProperty("flex", `0 0 ${value}px`, "important");
        chatter.style.setProperty("width", `${value}px`, "important");
        chatter.style.setProperty("max-width", `${value}px`, "important");
    } else {
        chatter.style.removeProperty("flex");
        chatter.style.removeProperty("width");
        chatter.style.removeProperty("max-width");
    }
}

function setupHandle(root) {
    if (!root) {
        return;
    }
    const chatter = root.querySelector(":scope .o-mail-Form-chatter.o-aside");
    root.querySelectorAll(".td_chatter_handle").forEach((h) => {
        if (!chatter || h.parentElement !== chatter) {
            h.remove();
        }
    });
    if (!chatter) {
        return;
    }
    applyWidth(chatter, readWidth());
    if (chatter.querySelector(":scope > .td_chatter_handle")) {
        return;
    }
    const handle = document.createElement("div");
    handle.className = "td_chatter_handle";
    handle.title = "";
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", "vertical");
    handle.addEventListener("pointerdown", (ev) => {
        ev.preventDefault();
        const startX = ev.clientX;
        const startWidth = chatter.getBoundingClientRect().width;
        const total = chatter.parentElement.getBoundingClientRect().width;
        document.documentElement.classList.add("td_chatter_resizing");
        const onMove = (move) => {
            // the chatter is on the right: dragging the handle to the left makes it wider
            applyWidth(chatter, clampChatterWidth(startWidth + (startX - move.clientX), total));
        };
        const onUp = () => {
            document.removeEventListener("pointermove", onMove);
            document.removeEventListener("pointerup", onUp);
            document.documentElement.classList.remove("td_chatter_resizing");
            writeWidth(Math.round(chatter.getBoundingClientRect().width));
        };
        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp);
    });
    handle.addEventListener("dblclick", () => {
        writeWidth(null);
        applyWidth(chatter, null);
    });
    chatter.prepend(handle);
}

if (isTdEeLook()) {
    patch(FormRenderer.prototype, {
        setup() {
            super.setup(...arguments);
            const rootRef = useRef("compiled_view_root");
            const update = () => setupHandle(rootRef.el);
            onMounted(update);
            onPatched(update);
        },
    });
}
