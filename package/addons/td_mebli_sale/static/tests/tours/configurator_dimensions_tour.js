import { registry } from "@web/core/registry";

// D-15 (A-11-7): the tour does not depend on the start menu of «Sales» nor on the language of the user: it opens the
// action of the quotations directly and finds the elements by fields and classes, never by an English text of the
// interface (only the names of the test data: the customer, the product, the attributes).
// D-02: the new order is created and SAVED from the form (the salesperson of the showroom runs the tour).
// D-04 / AC-015: the width typed in the line changes the price (checked by the Python test after the tour).
const dialog = ".o_sale_product_configurator_dialog";

function setDimension(attributeName, value) {
    return {
        content: `Set ${attributeName} = ${value}`,
        trigger: `${dialog} div[name="ptal"]:has(label:contains("${attributeName}")) input[type="text"]`,
        run: `edit ${value} && click ${dialog} .modal-body`,
    };
}

registry.category("web_tour.tours").add("td_mebli_sale_configurator_tour", {
    url: "/odoo/action-sale.action_quotations_with_onboarding",
    steps: () => [
        { content: "The list of the quotations", trigger: ".o_list_view .o_list_button_add", run: "click" },
        { content: "A new order", trigger: ".o_form_view .o_field_widget[name=partner_id] input", run: "edit Test customer" },
        { trigger: 'ul.ui-autocomplete a:contains("Test customer")', run: "click" },
        {
            content: "Add a product (the first control of the lines)",
            trigger: 'div[name="order_line"] .o_field_x2many_list_row_add a:not(.ml16)',
            run: "click",
        },
        { trigger: 'div[name="order_line"] .o_data_row div[name="product_template_id"] input', run: "edit Cabinet" },
        { trigger: 'ul.ui-autocomplete a:contains("Cabinet")', run: "click" },
        setDimension("Width, mm", "1000"),
        setDimension("Height, mm", "700"),
        setDimension("Depth, mm", "500"),
        { content: "Confirm the configurator", trigger: `${dialog} .modal-footer button.btn-primary`, run: "click" },
        { content: "The configurator is closed", trigger: `body:not(:has(${dialog}))` },
        // numbers are not compared on the screen: their format follows the language (1 000 in uk_UA)
        { trigger: 'div[name="order_line"] .o_data_row td[name="product_template_id"]:contains("Cabinet")' },
        { content: "Save the new order", trigger: ".o_form_button_save:enabled", run: "click" },
        { content: "The order is saved (D-02)", trigger: ".o_form_saved" },
        {
            content: "Change the width in the line (AC-015)",
            trigger: 'div[name="order_line"] .o_data_row td[name="td_width"]',
            run: "click",
        },
        { trigger: 'div[name="order_line"] .o_data_row div[name="td_width"] input', run: "edit 1200" },
        { content: "Leave the cell", trigger: ".o_form_view .o_field_widget[name=partner_id]", run: "click" },
        { content: "Save the new width", trigger: ".o_form_button_save:enabled", run: "click" },
        { content: "The order is saved again", trigger: ".o_form_saved" },
    ],
});
