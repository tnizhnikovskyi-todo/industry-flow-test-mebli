import { registry } from "@web/core/registry";

// D-03 (A-11-7): the form of the measurement sheet opens for every role (no «Oh snap!»: an error of the client fails the
// tour). Selectors by fields only, the language of the user does not matter.
registry.category("web_tour.tours").add("td_mebli_measure_form_tour", {
    steps: () => [
        { content: "The form is shown", trigger: ".o_form_view .o_field_widget[name=room]" },
        { content: "The order field is shown", trigger: ".o_form_view .o_field_widget[name=order_id]" },
        { content: "The niches", trigger: ".o_form_view .o_field_widget[name=niche_ids]" },
        { content: "No error dialog", trigger: "body:not(:has(.o_error_dialog))" },
    ],
});
