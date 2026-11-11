import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";
import configuratorTourUtils from "@sale/js/tours/product_configurator_tour_utils";
import tourUtils from "@sale/js/tours/tour_utils";

registry.category("web_tour.tours").add("td_mebli_sale_configurator_tour", {
    url: "/odoo",
    steps: () => [
        ...stepUtils.goToAppSteps("sale.sale_menu_root", "Go to the Sales App"),
        ...tourUtils.createNewSalesOrder(),
        ...tourUtils.selectCustomer("Test customer"),
        ...tourUtils.addProduct("Cabinet"),
        configuratorTourUtils.setCustomAttribute("Cabinet", "Width, mm", "1000"),
        configuratorTourUtils.setCustomAttribute("Cabinet", "Height, mm", "700"),
        configuratorTourUtils.setCustomAttribute("Cabinet", "Depth, mm", "500"),
        ...configuratorTourUtils.saveConfigurator(),
        ...stepUtils.saveForm(),
    ],
});
