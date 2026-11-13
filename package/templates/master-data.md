# Опис довідників майстер-даних пакета mebli (A-13)

Каркас — `master-data-template-builder/references/master-data-template.md`. Файли й порядок — `package/master-data/README.md`. Типи й обов'язковість — `fields_get` чистої тестової бази Odoo 19.0 CE з модулями профілю A (2026-11-13). Приклади вигадані; ціни, норми часу й суми в прикладах порожні.

## Категорії номенклатури (migration.md №3) (`product.category`, файл `01_product.category.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): категорії номенклатури (migration.md №3).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `parent_id/id` | many2one → product.category | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | parent_id/id |
|---|---|---|
| td_md.product_category_raw | Сировина |  |
| td_md.product_category_boards | Плитні матеріали | td_md.product_category_raw |
Залежності: файли з NN нижче за 01 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 01.

## Постачальники й покупці (№6, №17) (`res.partner`, файл `02_res.partner.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): постачальники й покупці (№6, №17).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | ні | Odoo `fields_get` |  |
| `is_company` | boolean | ні | Odoo `fields_get` |  |
| `supplier_rank` | integer | ні | Odoo `fields_get` |  |
| `customer_rank` | integer | ні | Odoo `fields_get` |  |
| `vat` | char | ні | Odoo `fields_get` |  |
| `company_registry` | char | ні | Odoo `fields_get` |  |
| `phone` | char | ні | Odoo `fields_get` |  |
| `email` | char | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | is_company | supplier_rank | customer_rank | vat | company_registry | phone | email |
|---|---|---|---|---|---|---|---|---|
| td_md.res_partner_demo_dsp | ТОВ "Демо-Постачальник ДСП" | True | 1 | 0 |  |  |  |  |
| td_md.res_partner_demo_fittings | ТОВ "Демо-Фурнітура" | True | 1 | 0 |  |  |  |  |
Залежності: файли з NN нижче за 02 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 02.

## Атрибути конфігуратора (№7, AC-011) (`product.attribute`, файл `03_product.attribute.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): атрибути конфігуратора (№7, AC-011).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `create_variant` | selection | ні | Odoo `fields_get` | значення: always, dynamic, no_variant |
| `display_type` | selection | ні | Odoo `fields_get` | значення: radio, pills, select, color, multi, image |
Приклади рядків (вигадані):
| id | name | create_variant | display_type |
|---|---|---|---|
| td_md.product_attribute_decor | Декор | no_variant | radio |
| td_md.product_attribute_edge | Кромка | no_variant | radio |
Залежності: файли з NN нижче за 03 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 03.

## Значення атрибутів (№7) (`product.attribute.value`, файл `04_product.attribute.value.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): значення атрибутів (№7).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `attribute_id/id` | many2one → product.attribute | так | Odoo `fields_get` |  |
| `sequence` | integer | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | attribute_id/id | sequence |
|---|---|---|---|
| td_md.product_attribute_value_decor_white | Білий | td_md.product_attribute_decor | 1 |
| td_md.product_attribute_value_decor_oak | Дуб світлий | td_md.product_attribute_decor | 2 |
Залежності: файли з NN нижче за 04 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 04.

## Матеріали, фурнітура, замовні позиції (№4, №5, AC-024) (`product.product`, файл `05_product.product.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): матеріали, фурнітура, замовні позиції (№4, №5, AC-024).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `default_code` | char | ні | Odoo `fields_get` |  |
| `type` | selection | ні | Odoo `fields_get` | значення: consu, service, combo |
| `is_storable` | boolean | ні | Odoo `fields_get` |  |
| `categ_id/id` | many2one → product.category | ні | Odoo `fields_get` |  |
| `uom_id/id` | many2one → uom.uom | ні | Odoo `fields_get` |  |
| `sale_ok` | boolean | ні | Odoo `fields_get` |  |
| `purchase_ok` | boolean | ні | Odoo `fields_get` |  |
| `route_ids/id` | many2many → stock.route | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | default_code | type | is_storable | categ_id/id | uom_id/id | sale_ok | purchase_ok | route_ids/id |
|---|---|---|---|---|---|---|---|---|---|
| td_md.product_product_dsp_18_w | Плита ДСП 18 мм біла | DSP-18-W | consu | True | td_md.product_category_boards | uom.product_uom_square_meter | False | True |  |
| td_md.product_product_dsp_18_oak | Плита ДСП 18 мм дуб світлий | DSP-18-OAK | consu | True | td_md.product_category_boards | uom.product_uom_square_meter | False | True |  |
Залежності: файли з NN нижче за 05 (колонки `/id`); стандартні xmlid: `purchase_stock.route_warehouse0_buy`, `stock.route_warehouse0_mto`, `uom.product_uom_meter`, `uom.product_uom_square_meter`, `uom.product_uom_unit`.
Порядок імпорту: 05.

## Вироби (№7) (`product.template`, файл `06_product.template.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): вироби (№7).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `default_code` | char | ні | Odoo `fields_get` |  |
| `type` | selection | ні | Odoo `fields_get` | значення: consu, service, combo |
| `is_storable` | boolean | ні | Odoo `fields_get` |  |
| `categ_id/id` | many2one → product.category | ні | Odoo `fields_get` |  |
| `uom_id/id` | many2one → uom.uom | ні | Odoo `fields_get` |  |
| `sale_ok` | boolean | ні | Odoo `fields_get` |  |
| `purchase_ok` | boolean | ні | Odoo `fields_get` |  |
| `route_ids/id` | many2many → stock.route | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | default_code | type | is_storable | categ_id/id | uom_id/id | sale_ok | purchase_ok | route_ids/id |
|---|---|---|---|---|---|---|---|---|---|
| td_md.product_template_wardrobe_01 | Шафа-купе | WARDROBE-01 | consu | True | td_md.product_category_cabinet | uom.product_uom_unit | True | False | mrp.route_warehouse0_manufacture,stock.route_warehouse0_mto |
| td_md.product_template_bedside_01 | Тумба приліжкова | BEDSIDE-01 | consu | True | td_md.product_category_cabinet | uom.product_uom_unit | True | False | mrp.route_warehouse0_manufacture,stock.route_warehouse0_mto |
Залежності: файли з NN нижче за 06 (колонки `/id`); стандартні xmlid: `mrp.route_warehouse0_manufacture`, `stock.route_warehouse0_mto`, `uom.product_uom_unit`.
Порядок імпорту: 06.

## Атрибути виробу (№7, AC-011) (`product.template.attribute.line`, файл `07_product.template.attribute.line.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): атрибути виробу (№7, AC-011).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `product_tmpl_id/id` | many2one → product.template | так | Odoo `fields_get` |  |
| `attribute_id/id` | many2one → product.attribute | так | Odoo `fields_get` |  |
| `value_ids/id` | many2many → product.attribute.value | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | product_tmpl_id/id | attribute_id/id | value_ids/id |
|---|---|---|---|
| td_md.product_template_attribute_line_wardrobe_decor | td_md.product_template_wardrobe_01 | td_md.product_attribute_decor | td_md.product_attribute_value_decor_white,td_md.product_attribute_value_decor_oak,td_md.product_attribute_value_decor_graphite |
| td_md.product_template_attribute_line_wardrobe_edge | td_md.product_template_wardrobe_01 | td_md.product_attribute_edge | td_md.product_attribute_value_edge_white,td_md.product_attribute_value_edge_oak,td_md.product_attribute_value_edge_graphite |
Залежності: файли з NN нижче за 07 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 07.

## Ціни й строки постачальників (№6, AC-085) (`product.supplierinfo`, файл `08_product.supplierinfo.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): ціни й строки постачальників (№6, AC-085).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `partner_id/id` | many2one → res.partner | так | Odoo `fields_get` |  |
| `product_id/id` | many2one → product.product | ні | Odoo `fields_get` |  |
| `min_qty` | float | ні | Odoo `fields_get` |  |
| `delay` | integer | ні | Odoo `fields_get` |  |
| `price` | float | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | partner_id/id | product_id/id | min_qty | delay | price |
|---|---|---|---|---|---|
| td_md.product_supplierinfo_dsp_18_w | td_md.res_partner_demo_dsp | td_md.product_product_dsp_18_w | 1 | 3 |  |
| td_md.product_supplierinfo_edge_pvc_2_w | td_md.res_partner_demo_dsp | td_md.product_product_edge_pvc_2_w | 1 | 3 |  |
Залежності: файли з NN нижче за 08 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 08.

## Дільниці (№9) (`mrp.workcenter`, файл `09_mrp.workcenter.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): дільниці (№9).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | ні | Odoo `fields_get` |  |
| `code` | char | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | code |
|---|---|---|
| td_md.mrp_workcenter_cutting | Розкрій | CUT |
| td_md.mrp_workcenter_edging | Кромкування | EDGE |
Залежності: файли з NN нижче за 09 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 09.

## Специфікації виробів (№9) (`mrp.bom`, файл `10_mrp.bom.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): специфікації виробів (№9).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `product_tmpl_id/id` | many2one → product.template | так | Odoo `fields_get` |  |
| `product_qty` | float | ні | Odoo `fields_get` |  |
| `type` | selection | ні | Odoo `fields_get` | значення: normal, phantom |
| `code` | char | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | product_tmpl_id/id | product_qty | type | code |
|---|---|---|---|---|
| td_md.mrp_bom_wardrobe_01 | td_md.product_template_wardrobe_01 | 1 | normal | BOM-WARDROBE-01 |
| td_md.mrp_bom_bedside_01 | td_md.product_template_bedside_01 | 1 | normal | BOM-BEDSIDE-01 |
Залежності: файли з NN нижче за 10 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 10.

## Компоненти специфікацій (№9) (`mrp.bom.line`, файл `11_mrp.bom.line.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): компоненти специфікацій (№9).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `bom_id/id` | many2one → mrp.bom | так | Odoo `fields_get` |  |
| `product_id/id` | many2one → product.product | так | Odoo `fields_get` |  |
| `product_qty` | float | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | bom_id/id | product_id/id | product_qty |
|---|---|---|---|
| td_md.mrp_bom_line_wardrobe_dsp | td_md.mrp_bom_wardrobe_01 | td_md.product_product_dsp_18_w | 6.5 |
| td_md.mrp_bom_line_wardrobe_hdf | td_md.mrp_bom_wardrobe_01 | td_md.product_product_hdf_3_w | 2.4 |
Залежності: файли з NN нижче за 11 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 11.

## Операції маршруту (№9) (`mrp.routing.workcenter`, файл `12_mrp.routing.workcenter.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): операції маршруту (№9).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `bom_id/id` | many2one → mrp.bom | так | Odoo `fields_get` |  |
| `workcenter_id/id` | many2one → mrp.workcenter | так | Odoo `fields_get` |  |
| `sequence` | integer | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | bom_id/id | workcenter_id/id | sequence |
|---|---|---|---|---|
| td_md.mrp_routing_workcenter_wardrobe_cut | Розкрій плит | td_md.mrp_bom_wardrobe_01 | td_md.mrp_workcenter_cutting | 10 |
| td_md.mrp_routing_workcenter_wardrobe_edge | Кромкування деталей | td_md.mrp_bom_wardrobe_01 | td_md.mrp_workcenter_edging | 20 |
Залежності: файли з NN нижче за 12 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 12.

## Працівники й PIN (№12, AC-077) (`hr.employee`, файл `13_hr.employee.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): працівники й PIN (№12, AC-077).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | ні | Odoo `fields_get` |  |
| `job_title` | char | ні | Odoo `fields_get` |  |
| `pin` | char | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | job_title | pin |
|---|---|---|---|
| td_md.hr_employee_cutter_1 | Розкрійник 1 | Оператор розкрою |  |
| td_md.hr_employee_assembler_1 | Збиральник 1 | Збиральник |  |
Залежності: файли з NN нижче за 13 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 13.

## Обладнання (№11) (`maintenance.equipment`, файл `14_maintenance.equipment.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): обладнання (№11).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name |
|---|---|
| td_md.maintenance_equipment_panel_saw | Форматно-розкрійний верстат |
| td_md.maintenance_equipment_edge_bander | Кромкооблицювальний верстат |
Залежності: файли з NN нижче за 14 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 14.

## Прайс-листи (BOX §3) (`product.pricelist`, файл `15_product.pricelist.csv`, трек: стандарт/майстер-дані)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): прайс-листи (BOX §3).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `name` | char | так | Odoo `fields_get` |  |
| `currency_id/id` | many2one → res.currency | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | name | currency_id/id |
|---|---|---|
| td_md.product_pricelist_fittings_eur | Прайс фурнітури (EUR) | base.EUR |
Залежності: файли з NN нижче за 15 (колонки `/id`); стандартні xmlid: `base.EUR`.
Порядок імпорту: 15.

## Поля матеріалу td_* (№4) (`product.product`, файл `td/05b_product.product.csv`, трек: код (A-11), потребує модулів A-11)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): поля матеріалу td_* (№4).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `td_material_kind` | selection | ні | Odoo `fields_get` | значення: board, edge, fitting, facade, cutting |
| `td_sheet_length_mm` | integer | ні | Odoo `fields_get` |  |
| `td_sheet_width_mm` | integer | ні | Odoo `fields_get` |  |
| `td_thickness_mm` | float | ні | Odoo `fields_get` |  |
| `td_waste_pct` | float | ні | Odoo `fields_get` |  |
| `td_edge_thickness` | float | ні | Odoo `fields_get` |  |
| `td_matches_board_id/id` | many2one → product.product | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | td_material_kind | td_sheet_length_mm | td_sheet_width_mm | td_thickness_mm | td_waste_pct | td_edge_thickness | td_matches_board_id/id |
|---|---|---|---|---|---|---|---|
| td_md.product_product_dsp_18_w | board | 2800 | 2070 | 18 | 15 |  |  |
| td_md.product_product_dsp_18_oak | board | 2800 | 2070 | 18 | 15 |  |  |
Залежності: файли з NN нижче за 05b (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 05b (другий прохід тих самих id, після стандартного файлу).

## Параметричний виріб td_* (№7) (`product.template`, файл `td/06b_product.template.csv`, трек: код (A-11), потребує модулів A-11)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): параметричний виріб td_* (№7).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `td_is_parametric` | boolean | ні | Odoo `fields_get` |  |
| `td_width_nominal` | integer | ні | Odoo `fields_get` |  |
| `td_height_nominal` | integer | ні | Odoo `fields_get` |  |
| `td_depth_nominal` | integer | ні | Odoo `fields_get` |  |
| `td_width_min` | integer | ні | Odoo `fields_get` |  |
| `td_width_max` | integer | ні | Odoo `fields_get` |  |
| `td_height_min` | integer | ні | Odoo `fields_get` |  |
| `td_height_max` | integer | ні | Odoo `fields_get` |  |
| `td_depth_min` | integer | ні | Odoo `fields_get` |  |
| `td_depth_max` | integer | ні | Odoo `fields_get` |  |
| `td_edge_allowance_mm` | integer | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | td_is_parametric | td_width_nominal | td_height_nominal | td_depth_nominal | td_width_min | td_width_max | td_height_min | td_height_max | td_depth_min | td_depth_max | td_edge_allowance_mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| td_md.product_template_wardrobe_01 | True | 1800 | 2400 | 600 | 1000 | 3000 | 2000 | 2700 | 400 | 700 | 2 |
| td_md.product_template_bedside_01 | True | 450 | 500 | 400 | 350 | 600 | 400 | 700 | 300 | 500 | 2 |
Залежності: файли з NN нижче за 06b (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 06b (другий прохід тих самих id, після стандартного файлу).

## Норми й розцінки td_* (№9) (`mrp.routing.workcenter`, файл `td/12b_mrp.routing.workcenter.csv`, трек: код (A-11), потребує модулів A-11)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): норми й розцінки td_* (№9).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `td_time_basis` | selection | ні | Odoo `fields_get` | значення: fixed, per_part, per_edge_m, per_board_m2 |
| `td_time_rate` | float | ні | Odoo `fields_get` |  |
| `td_piece_rate` | monetary | ні | Odoo `fields_get` |  |
| `td_quality_point` | char | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | td_time_basis | td_time_rate | td_piece_rate | td_quality_point |
|---|---|---|---|---|
| td_md.mrp_routing_workcenter_wardrobe_cut | per_board_m2 |  |  |  |
| td_md.mrp_routing_workcenter_wardrobe_edge | per_edge_m |  |  | Кромка без сколів |
Залежності: файли з NN нижче за 12b (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 12b (другий прохід тих самих id, після стандартного файлу).

## Правила деталей (№8) (`td.mebli.part.rule`, файл `td/16_td.mebli.part.rule.csv`, трек: код (A-11), потребує модулів A-11)
Призначення (ТР `package/tr/migration.md` §1, BOX §3): правила деталей (№8).
| Поле (колонка CSV) | Тип | Обов'язкове | Звідки | Примітка |
|---|---|---|---|---|
| `id` | external ID | так | формат пакета | `td_md.<model_slug>_<slug>` |
| `product_tmpl_id/id` | many2one → product.template | так | Odoo `fields_get` |  |
| `sequence` | integer | ні | Odoo `fields_get` |  |
| `name` | char | так | Odoo `fields_get` |  |
| `qty` | integer | ні | Odoo `fields_get` |  |
| `material_role` | selection | ні | Odoo `fields_get` | значення: body_board, facade_board, fixed |
| `len_w` | float | ні | Odoo `fields_get` |  |
| `len_h` | float | ні | Odoo `fields_get` |  |
| `len_const` | float | ні | Odoo `fields_get` |  |
| `wid_d` | float | ні | Odoo `fields_get` |  |
| `wid_const` | float | ні | Odoo `fields_get` |  |
| `edge_long_sides` | integer | ні | Odoo `fields_get` |  |
| `edge_short_sides` | integer | ні | Odoo `fields_get` |  |
Приклади рядків (вигадані):
| id | product_tmpl_id/id | sequence | name | qty | material_role | len_w | len_h | len_const | wid_d | wid_const | edge_long_sides | edge_short_sides |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| td_md.td_mebli_part_rule_wardrobe_side | td_md.product_template_wardrobe_01 | 10 | Бокова стінка | 2 | body_board | 0 | 1 | 0 | 1 | 0 | 1 | 0 |
| td_md.td_mebli_part_rule_wardrobe_top | td_md.product_template_wardrobe_01 | 20 | Дах і дно | 2 | body_board | 1 | 0 | -36 | 1 | 0 | 1 | 0 |
Залежності: файли з NN нижче за 16 (колонки `/id`); стандартні xmlid: —.
Порядок імпорту: 16.
