# Шаблони майстер-даних пакета mebli (версія 1.3, A-13 спроба 4 — повтор за `package/CHECKS.md` №28; версія 1.2 — спроба 3, №7, №27)

База коду: SHA `4e96a56` (гілка `flow/A-12-2-test`; спроба 2 — `4e0fdda`, спроба 1 — `351d4a8`) | ТР: `package/SPEC.md`, `package/tr/migration.md` §1 @`4e0fdda` | ALLOCATION: `package/ALLOCATION.md`@`4e0fdda` | CONFIG: `package/config/CONFIG.md` (A-12 спроба 2, та сама гілка, не закомічено на момент A-13) | модулі: `package/addons/`@`4e0fdda` | BOX: `docs/industries/mebli/research/BOX.md` §3–4@`4e0fdda`

Скіл: `flow-package-build:master-data-template-builder (версія 0.3.1)`. Формат — `master-data-format.md` (UTF-8, `,`, перший стовпець `id` = `td_md.<model_slug>_<slug>`, many2one / many2many — `<поле>/id`). Усі приклади **вигадані** (контрагенти «Демо-…», без ПІБ, телефонів, email, ЄДРПОУ, IBAN); кількості — ілюстративні; **ціни, норми часу, години й суми — порожні** (заповнює клієнт у B-06; правило тесту «без годин і грошей»).

## Файли

| Файл | Модель | Рядків | Призначення (розділ/AC ТР) |
|---|---|---|---|
| `01_product.category.csv` | `product.category` | 8 | `tr/migration.md` §1 №3; категорії номенклатури (BOX §3) |
| `02_res.partner.csv` | `res.partner` | 5 | №6, №17; постачальники плит, фурнітури, фасадів, порізки (AC-024, AC-085, AC-026); покупець-компанія |
| `03_product.attribute.csv` | `product.attribute` | 2 | №7; декор і кромка для конфігуратора (AC-011, коробка B) |
| `04_product.attribute.value.csv` | `product.attribute.value` | 6 | №7; значення декору й кромки |
| `05_product.product.csv` | `product.product` | 10 | №4, №5; плити (декори білий / дуб / графіт), кромка до кожного декору, фурнітура, замовний фасад (маршрут MTO; «Купити» — від складу, AC-024) |
| `06_product.template.csv` | `product.template` | 2 | №7; вироби «Шафа-купе», «Тумба» (маршрут MTO; «Виробництво» — від складу) |
| `07_product.template.attribute.line.csv` | `product.template.attribute.line` | 2 | №7; атрибути виробу (AC-011) |
| `08_product.supplierinfo.csv` | `product.supplierinfo` | 4 | №6; ціни й строки постачальників (AC-024, AC-085) |
| `09_mrp.workcenter.csv` | `mrp.workcenter` | 4 | №9; дільниці розкрій, кромкування, присадка, збирання |
| `10_mrp.bom.csv` | `mrp.bom` | 2 | №9; шаблони специфікацій виробів |
| `11_mrp.bom.line.csv` | `mrp.bom.line` | 5 | №9; компоненти специфікацій. Плиту й кромку корпусу параметричного виробу з правилами деталей («Шафа-купе») сюди **не** вносять: їх дає специфікація замовлення з деталей (AC-013); у шаблоні — лише те, чого деталі не дають (ДВП задньої стінки, замовний фасад). «Тумба» без правил деталей — стандартна BoM, її рядки плити й кромки лишаються (CHECKS №28) |
| `12_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` | 5 | №9; операції маршруту (норми часу — порожньо) |
| `13_hr.employee.csv` | `hr.employee` | 3 | №12; працівники (PIN кіоску, AC-077 — порожньо, задає клієнт) |
| `14_maintenance.equipment.csv` | `maintenance.equipment` | 2 | №11; обладнання (зв'язок з дільницею — `td_mebli_maint`, A-11) |
| `15_product.pricelist.csv` | `product.pricelist` | 1 | BOX §3 «Прайс-листи й валюта (EUR для фурнітури)» |
| `td/05b_product.product.csv` | `product.product` (поля `td_*`) | 8 | №4; вид матеріалу, формат листа, товщина, % відходу, кромка ↔ плита |
| `td/03b_product.attribute.csv` | `product.attribute` (поле `td_component_role`) | 2 | №7, AC-011; роль атрибута в специфікації замовлення: декор → `body_board`, кромка → `edge` (CHECKS №7) |
| `td/04b_product.attribute.value.csv` | `product.attribute.value` (поля `td_component_product_id`, `td_edge_thickness`) | 6 | №7, AC-011; декор → плита корпусу, кромка → товщина, мм (CHECKS №7) |
| `td/06b_product.template.csv` | `product.template` (поля `td_*`) | 2 | №7; параметричний виріб, розміри й межі |
| `td/12b_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` (поля `td_*`) | 3 | №9; база норми, норма, розцінка (порожньо), контрольна точка |
| `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | 2 | №8; правила деталей виробу |
| `td/01b_product.category.csv` | `product.category` (поле `td_warranty_months`) | 1 | №3, AC-111; строк гарантії категорії — **порожньо** до висновку юриста (№17), заповнює клієнт |
| `td/14b_maintenance.equipment.csv` | `maintenance.equipment` (поле `td_workcenter_id`) | 2 | №11, AC-076; верстат ↔ дільниця |
| `td/17_td.mebli.accrual.reason.csv` | `td.mebli.accrual.reason` | 3 | №14, AC-107; причини премій і штрафів (суми порожні) |
| `td/18_td.mebli.import.template.csv` | `td.mebli.import.template` | 1 | №16, AC-049 (G2); шаблон мапінгу колонок файлу деталей (`header_signature`, `mapping_json`) |
| `td/19b_res.partner.csv` | `res.partner` (поле `td_bas_code`) | 2 | AC-039…AC-042, VP-04; код контрагента BAS (лише з `td_mebli_bas`) |
| `td/20b_product.product.csv` | `product.product` (поле `td_bas_code`) | 2 | те саме; код номенклатури BAS |
| `td/21b_hr.employee.csv` | `hr.employee` (поле `td_bas_code`) | 2 | те саме; табельний код BAS |

## Порядок імпорту

Джерело-перелік (вимога): `package/config/CONFIG.md` «Модулі до установки», профіль `ce` / коробка A (`manifest.yaml`, без `when:` + `td_mebli_bas` при VP-04 = `true`; без `td_mebli_multico`): base_setup, mail, calendar, portal, hr, crm, stock, mrp, project, account, sale_crm, sale_margin, sale_stock, sale_mrp, sale_project, purchase, purchase_stock, sale_purchase_stock, purchase_mrp, mrp_account, repair, l10n_ua, hr_attendance, hr_hourly_cost, maintenance, base_import, td_mebli_base, td_mebli_mrp, td_mebli_sale, td_mebli_measure, td_mebli_cutting, td_mebli_purchase, td_mebli_ua, td_mebli_shop, td_mebli_install, td_mebli_claim, td_mebli_cost, td_mebli_maint, td_mebli_attendance, td_mebli_bas, td_mebli_migration, td_mebli_dashboard, td_mebli_notify (43 модулів).

Фактично installed у тестовій базі `test-mebli-r3cfg-A` (спроба 3; 137 модулів — той самий список, що в спробі 2; повний список): account, account_add_gln, account_edi_ubl_cii, account_payment, analytic, api_doc, auth_passkey, auth_passkey_portal, auth_signup, auth_totp, auth_totp_mail, auth_totp_portal, barcodes, barcodes_gs1_nomenclature, base, base_geolocalize, base_import, base_import_module, base_install_request, base_setup, bus, calendar, calendar_sms, contacts, crm, crm_iap_enrich, crm_iap_mine, crm_sms, digest, google_gmail, hr, hr_attendance, hr_calendar, hr_homeworking, hr_homeworking_calendar, hr_hourly_cost, hr_maintenance, hr_org_chart, hr_skills, html_editor, http_routing, iap, iap_crm, iap_mail, l10n_ua, mail, mail_bot, mail_bot_hr, maintenance, microsoft_outlook, mrp, mrp_account, mrp_repair, onboarding, partner_autocomplete, payment, phone_validation, portal, portal_rating, privacy_lookup, product, project, project_account, project_hr_skills, project_mrp, project_mrp_account, project_mrp_sale, project_purchase, project_purchase_stock, project_sms, project_stock, project_stock_account, project_todo, purchase, purchase_edi_ubl_bis3, purchase_mrp, purchase_repair, purchase_stock, rating, repair, resource, resource_mail, rpc, sale, sale_crm, sale_edi_ubl, sale_management, sale_margin, sale_mrp, sale_pdf_quote_builder, sale_project, sale_project_stock, sale_project_stock_account, sale_purchase, sale_purchase_project, sale_purchase_stock, sale_service, sale_sms, sale_stock, sale_stock_margin, sales_team, sms, snailmail, snailmail_account, spreadsheet, spreadsheet_account, spreadsheet_dashboard, spreadsheet_dashboard_account, spreadsheet_dashboard_sale, spreadsheet_dashboard_stock_account, stock, stock_account, stock_maintenance, stock_sms, td_mebli_attendance, td_mebli_bas, td_mebli_base, td_mebli_claim, td_mebli_cost, td_mebli_cutting, td_mebli_dashboard, td_mebli_install, td_mebli_maint, td_mebli_measure, td_mebli_migration, td_mebli_mrp, td_mebli_notify, td_mebli_purchase, td_mebli_sale, td_mebli_shop, td_mebli_ua, uom, utm, web, web_hierarchy, web_tour, web_unsplash.

Перевірка MD-modules: джерело-перелік ⊆ installed — так (43/43, усі 26 стандартних і 17 `td_mebli_*` профілю A). Розбіжність CONFIG ↔ ALLOCATION — немає (CONFIG = ALLOCATION профілю A).

| NN | Файл | Модель | Залежить від | Рядків | Модулі |
|---|---|---|---|---|---|
| 01 | `01_product.category.csv` | `product.category` | — (батьки — вище в тому ж файлі) | 8 | product |
| 02 | `02_res.partner.csv` | `res.partner` | — | 5 | base (+ `supplier_rank`/`customer_rank`: account, purchase) |
| 03 | `03_product.attribute.csv` | `product.attribute` | — | 2 | product |
| 04 | `04_product.attribute.value.csv` | `product.attribute.value` | 03 | 6 | product |
| 05 | `05_product.product.csv` | `product.product` | 01; xmlid `uom.*`, `stock.route_warehouse0_mto` | 10 | product, stock |
| 06 | `06_product.template.csv` | `product.template` | 01; xmlid `uom.product_uom_unit`, `stock.route_warehouse0_mto` | 2 | product, stock |
| 07 | `07_product.template.attribute.line.csv` | `product.template.attribute.line` | 03, 04, 06 | 2 | product |
| 08 | `08_product.supplierinfo.csv` | `product.supplierinfo` | 02, 05 | 4 | product, purchase |
| 09 | `09_mrp.workcenter.csv` | `mrp.workcenter` | — | 4 | mrp |
| 10 | `10_mrp.bom.csv` | `mrp.bom` | 06 | 2 | mrp |
| 11 | `11_mrp.bom.line.csv` | `mrp.bom.line` | 05, 10 | 5 | mrp |
| 12 | `12_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` | 09, 10 | 5 | mrp |
| 13 | `13_hr.employee.csv` | `hr.employee` | — | 3 | hr (`pin` — hr_attendance) |
| 14 | `14_maintenance.equipment.csv` | `maintenance.equipment` | — | 2 | maintenance |
| 15 | `15_product.pricelist.csv` | `product.pricelist` | xmlid `base.EUR` | 1 | product |
| td 03b | `td/03b_product.attribute.csv` | `product.attribute` (`td_component_role`) | 03 (другий прохід тих самих `id`) | 2 | td_mebli_mrp |
| td 04b | `td/04b_product.attribute.value.csv` | `product.attribute.value` (`td_component_product_id`, `td_edge_thickness`) | 04 (другий прохід), 05 (`td_component_product_id/id`) | 6 | td_mebli_mrp |
| td 05b | `td/05b_product.product.csv` | `product.product` (`td_*`) | 05 (другий прохід тих самих `id`) | 8 | td_mebli_mrp |
| td 06b | `td/06b_product.template.csv` | `product.template` (`td_*`) | 06 | 2 | td_mebli_mrp |
| td 12b | `td/12b_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` (`td_*`) | 12 | 3 | td_mebli_mrp, td_mebli_shop |
| td 16 | `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | 06 | 2 | td_mebli_mrp |
| td 01b | `td/01b_product.category.csv` | `product.category` (`td_warranty_months`) | 01 (другий прохід тих самих `id`) | 1 | td_mebli_base |
| td 14b | `td/14b_maintenance.equipment.csv` | `maintenance.equipment` (`td_workcenter_id`) | 14, 09 | 2 | td_mebli_maint |
| td 17 | `td/17_td.mebli.accrual.reason.csv` | `td.mebli.accrual.reason` | — | 3 | td_mebli_install |
| td 18 | `td/18_td.mebli.import.template.csv` | `td.mebli.import.template` | xmlid `base.main_company` | 1 | td_mebli_mrp |
| td 19b | `td/19b_res.partner.csv` | `res.partner` (`td_bas_code`) | 02 | 2 | td_mebli_bas (VP-04 = `true`; у профілі light не імпортувати) |
| td 20b | `td/20b_product.product.csv` | `product.product` (`td_bas_code`) | 05 | 2 | td_mebli_bas (VP-04) |
| td 21b | `td/21b_hr.employee.csv` | `hr.employee` (`td_bas_code`) | 13 | 2 | td_mebli_bas (VP-04) |

**Порядок імпорту (28 кроків, спроба 3):** `01`…`15` → `td/01b` → `td/03b` → `td/04b` → `td/05b` → `td/06b` → `td/12b` → `td/14b` → `td/16` → `td/17` → `td/18` → `td/19b` → `td/20b` → `td/21b` (light — без трьох останніх, 25 кроків). Файли `td/` — після всіх стандартних: другі проходи тих самих `id` додають поля `td_*`, тож стандартні `01`…`15` імпортуються й без модулів A-11 (перевірено в базі лише зі стандартними модулями, спроба 3).

Номер `NN` файлів `td/` = місце в загальному порядку: `01b`…`16` — після свого стандартного файла (за таблицею вище), `17`, `18` — нові довідники `td.*`, `19b`…`21b` — останні, бо `td_mebli_bas` є не в кожному профілі (light — без нього). Узгодження з `td_mebli_migration` (записи `td.mebli.migration.step`, `package/addons/td_mebli_migration/data/td_mebli_migration_step_data.xml`, 28 кроків, A-11 спроба 3+): кроки 1–15 = `01`…`15`, 16 = `td/01b`, 17 = `td/03b`, 18 = `td/04b`, 19–28 = `td/05b`, `td/06b`, `td/12b`, `td/14b`, `td/16`, `td/17`, `td/18`, `td/19b`, `td/20b`, `td/21b` — збігаються (ризик R3-M-01 закрито, спроба 4). Конвертор `td_mebli_migration/scripts/convert_bas.py` (`DRAFT_MAPPING`) дописує колонку `td_bas_code` у стандартні `02`, `05`, `13` — за цими шаблонами `td_bas_code` іде окремими файлами `td/19b`, `td/20b`, `td/21b`.

Стандартні записи, на які посилаються шаблони (звірено в `ir.model.data` тестової бази): `uom.product_uom_square_meter` (м²), `uom.product_uom_meter` (м), `uom.product_uom_unit` (штуки), `stock.route_warehouse0_mto` (у чистій базі архівний; активує конфіг-пакет A-12, `td_config.route_mto_active`), `base.EUR` (валюту активує клієнт/B-04).

**Маршрути «Купити» і «Виробництво» (CHECKS №27).** В Odoo 19 вони не призначаються товару: `purchase_stock.route_warehouse0_buy` і `mrp.route_warehouse0_manufacture` мають `product_selectable = False`, а `route_ids` товару має домен `product_selectable = True`, тож імпорт мовчки відкидав їх (`purchase_stock/data/purchase_stock_data.xml`, `stock/models/product.py` `route_ids`). Ці маршрути задає **склад**: галочки складу «Купувати для поповнення» (`buy_to_resupply`) і «Виробляти для поповнення» (`manufacture_to_resupply`), за замовчуванням увімкнені. У шаблонах товарів лишився тільки MTO (`stock.route_warehouse0_mto`, `product_selectable = True`); закупівлю чи виробництво Odoo обирає правилами складу: товар зі специфікацією (`10`) виробляється, товар із постачальником (`08`) закуповується. Перевірено (спроба 3): «Шафа-купе» SO → MO, фасад FACADE-PAINT SO → PO.

## Залежності між файлами

- `04` → `03`: `attribute_id/id`; `07` → `03`, `04`, `06`: `attribute_id/id`, `value_ids/id`, `product_tmpl_id/id`.
- `05`, `06` → `01`: `categ_id/id`; `08` → `02`, `05`: `partner_id/id`, `product_id/id` (`product_tmpl_id` обчислюється з варіанта).
- `10` → `06`: `product_tmpl_id/id`; `11` → `10`, `05`: `bom_id/id`, `product_id/id` (компоненти — лише з `05`, бо `product.template` з `06` не дає xmlid варіанту); `12` → `09`, `10`.
- Двопрохідні: `td/01b`, `td/03b`, `td/04b`, `td/05b`, `td/06b`, `td/12b`, `td/14b`, `td/19b`, `td/20b`, `td/21b` — другий прохід тих самих `id` з полями `td_*` (після `01`, `03`, `04`, `05`, `06`, `12`, `14`, `02`, `05`, `13`); `td/04b` → `05` (`td_component_product_id/id`); `td/14b` → `09` (`td_workcenter_id/id`); `td/16` → `06`; `td/18` → `base.main_company`. Циклів немає. Скрипт `check_master_data.py` (MD-order) вважає власником `id` останній файл, що його згадує, тож дає хибний FAIL на двопрохідних файлах (observation спроби 1).

## Трасування ТР -> шаблон

| Довідник/поле ТР (розділ, AC) | Модель Odoo | Трек ALLOCATION | Файл або позначка |
|---|---|---|---|
| №1 Компанії й параметри (`td_*` на компанії) | `res.company` | конфіг (VP, A-12) | `конфіг (A-12)` — `package/config/` (`td_config.param_*`, `td_config.company_*`) |
| №2 Одиниці: лист, м², п. м, шт, комплект | `uom.uom` | конфіг (BOX §3 «в коробці») | `конфіг (A-12)`; м², м, шт — стандартні xmlid; «лист», «комплект» — **Відкрите питання**: у конфіг-пакеті A-12 їх немає (немає AC в ALLOCATION) |
| №3 Категорії товарів | `product.category` | стандарт (майстер-дані, BOX §3) | `01_product.category.csv` |
| №3 Гарантія на категорію (`td_warranty_months`, AC-111) | `product.category` | код (`td_mebli_base`) | `td/01b_product.category.csv` (значення порожні до юриста, рішення №17) |
| №4 Плити, кромка, фурнітура | `product.product` | стандарт | `05_product.product.csv` |
| №4 Поля матеріалу `td_*` | `product.product` | код (`td_mebli_mrp`) | `td/05b_product.product.csv`; `td_bas_code` (`td_mebli_bas`) — `td/20b_product.product.csv` |
| №5 Замовні позиції (MTO + «Купити», AC-024) | `product.product` | конфіг (маршрут — A-12) + стандарт (товар) | `05_product.product.csv` (рядок `FACADE-PAINT`, маршрут MTO; «Купити» — правило складу `buy_to_resupply`, див. «Порядок імпорту») |
| №6 Ціни постачальників (AC-085) | `product.supplierinfo` | стандарт | `08_product.supplierinfo.csv` |
| №7 Вироби, атрибути (AC-011) | `product.template`, `product.attribute(.value)`, `product.template.attribute.line` | конфіг AC-011 (налаштування варіантів — A-12) + майстер-дані | `03`, `04`, `06`, `07` |
| №7 Виключення сумісності (AC-011, B) | `product.template.attribute.exclusion` | конфіг | **Відкрите питання**: рядки посилаються на `product.template.attribute.value` без стабільного xmlid — задаються на формі виробу (B-04) |
| №7 Розміри параметричного виробу | `product.template` (`td_*`) | код (`td_mebli_mrp`) | `td/06b_product.template.csv` |
| №7 Роль атрибута, компонент і товщина кромки значення (`td_component_role`, `td_component_product_id`, `td_edge_thickness`; без них замовлення параметричного виробу не підтверджується) | `product.attribute`, `product.attribute.value` (`td_*`) | код (`td_mebli_mrp`) | `td/03b_product.attribute.csv`, `td/04b_product.attribute.value.csv` (CHECKS №7) |
| №8 Правила деталей | `td.mebli.part.rule` | код | `td/16_td.mebli.part.rule.csv` |
| №9 Дільниці, операції, специфікації | `mrp.workcenter`, `mrp.bom`, `mrp.bom.line`, `mrp.routing.workcenter` | стандарт | `09`, `10`, `11`, `12` |
| №9 Норми й розцінки (`td_time_*`, `td_piece_rate`, `td_quality_point`) | `mrp.routing.workcenter` (`td_*`) | код | `td/12b_mrp.routing.workcenter.csv` |
| №9 Потужність дільниці (`td_capacity_hours`) | `mrp.workcenter` (`td_*`) | код | поля `td_*` на `mrp.workcenter` у модулях A-11 немає (`fields_get` тестової бази) — шаблону немає; стандартна потужність — `09` (години — без значень у тесті) |
| №10 Причини втрат | `mrp.workcenter.productivity.loss` | конфіг | `конфіг (A-12)` — `td_config.loss_*` |
| №11 Обладнання ↔ дільниці | `maintenance.equipment` (+ `td_workcenter_id`) | стандарт + код (`td_mebli_maint`) | `14_maintenance.equipment.csv` + `td/14b_maintenance.equipment.csv` |
| №12 Працівники, PIN, бригади | `hr.employee` | стандарт (AC-077) | `13_hr.employee.csv`; `td_bas_code` — `td/21b_hr.employee.csv`; бригада — моделі-довідника в A-11 немає (склад бригади — рядки акта `td.mebli.install.act.crew`, транзакційні дані), шаблону немає |
| №13 Умови оплати з етапами | `account.payment.term` / `.line` (`td_milestone`) | код + конфіг (VP-05) | `код (A-11)` — запис `td_mebli_sale.payment_term_td_furniture` (50/40/10 %, `td_milestone` order/install/act); `конфіг (A-12)` — активність за VP-05 і умова за замовчуванням покупців (спроба 3); шаблону A-13 немає |
| №14 Причини премій і штрафів (AC-107) | `td.mebli.accrual.reason` | код (`td_mebli_install`) | `td/17_td.mebli.accrual.reason.csv` (докстрінг моделі: «типовий набір — дані конфіг-пакета», але `td.*` у конфіг-пакеті заборонено — відкрите питання) |
| №15 Теги рекламацій | `repair.tags` | конфіг (`tr/migration.md`) | `конфіг (A-12)` — **Відкрите питання**: у конфіг-пакеті A-12 немає (немає AC в ALLOCATION) |
| №16 Шаблони мапінгу імпорту (AC-049, G2) | `td.mebli.import.template` | код (`td_mebli_mrp`) | `td/18_td.mebli.import.template.csv` |
| №17 Клієнти | `res.partner` | стандарт (B-06) | `02_res.partner.csv` (рядок покупця-компанії) |
| BOX §3 Прайс-листи (EUR) | `product.pricelist` | стандарт | `15_product.pricelist.csv` |
| AC-089, AC-090 Міграція (ALLOCATION: A-11 + A-13 шаблони) | ці шаблони | код + A-13 | усі файли вище; конвертори й звірка — `td_mebli_migration` (A-11) |

## Потребують модулів A-11

| Файл `td/` | Модель/поле td_* | Модуль A-11 | Хто перевіряє імпорт |
|---|---|---|---|
| `td/05b_product.product.csv` | `td_material_kind`, `td_sheet_length_mm`, `td_sheet_width_mm`, `td_thickness_mm`, `td_waste_pct`, `td_edge_thickness`, `td_matches_board_id` | `td_mebli_mrp` | A-14 (track-convergence) / A-15 |
| `td/03b_product.attribute.csv` | `td_component_role` | `td_mebli_mrp` | A-13 (тест-імпорт нижче), A-14 / A-15 |
| `td/04b_product.attribute.value.csv` | `td_component_product_id`, `td_edge_thickness` | `td_mebli_mrp` | те саме |
| `td/06b_product.template.csv` | `td_is_parametric`, `td_*_nominal`, `td_*_min`, `td_*_max`, `td_edge_allowance_mm` | `td_mebli_mrp` | A-14 / A-15 |
| `td/12b_mrp.routing.workcenter.csv` | `td_time_basis`, `td_time_rate`, `td_piece_rate`, `td_quality_point` | `td_mebli_mrp`, `td_mebli_shop` | A-14 / A-15 |
| `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | `td_mebli_mrp` | A-14 / A-15 |
| `td/01b_product.category.csv` | `td_warranty_months` | `td_mebli_base` | A-13 (тест-імпорт нижче), A-14 / A-15 |
| `td/14b_maintenance.equipment.csv` | `td_workcenter_id` | `td_mebli_maint` | те саме |
| `td/17_td.mebli.accrual.reason.csv` | `td.mebli.accrual.reason` | `td_mebli_install` | те саме |
| `td/18_td.mebli.import.template.csv` | `td.mebli.import.template` | `td_mebli_mrp` | те саме |
| `td/19b_res.partner.csv`, `td/20b_product.product.csv`, `td/21b_hr.employee.csv` | `td_bas_code` | `td_mebli_bas` (VP-04; не в light) | те саме |
| — (шаблону немає) | бригада (довідника немає), `td_capacity_hours` (поля немає) | — | — |

Модулі A-11 є в `package/addons` (@`4e96a56`), тому файли `td/` **додатково** пройшли тест-імпорт у ту саму базу після стандартних (скіл вимагає лише стандартні; результат — таблиця нижче). Колонки `td/` звірено з `fields_get` тестової бази.

## Тест-імпорт

**Спроба 4 (2026-11-13, CHECKS №28):** з `11_mrp.bom.line.csv` прибрано статичні рядки шаблону «Шафа-купе» `td_md.mrp_bom_line_wardrobe_dsp` (DSP-18-W 6,5 м²) і `td_md.mrp_bom_line_wardrobe_edge` (EDGE-PVC-2-W 22 м) — подвійний облік із рядками деталей, а для декорів «дуб» і «графіт» МО вимагало ще й білу плиту. Тест-імпорт: `test-mebli-a114-cfga` — профіль A, 43 модулі `manifest.yaml` (137 installed) з `td_mebli_mrp` 19.0.1.1.2 + конфіг-пакет A-12 спроби 4 (2 проходи, read-back 23/23 PASS) → 28 кроків: усі файли ok, помилок 0, `11` — 5 / 5, разом 97 рядків, xmlid `td_md.*` — 80. «Шафа-купе» SO → MO для трьох декорів: плита й кромка лише декору (білий: DSP-18-W 5,746 / EDGE-PVC-2-W 8,336; дуб: DSP-18-OAK / EDGE-PVC-2-OAK; графіт: DSP-18-GR / EDGE-PVC-2-GR — ті самі 5,746 / 8,336 = кількість з деталей), плюс HDF-3-W 2,4 і FACADE-PAINT 2,2 з шаблону; білої плити в МО дуба й графіту немає. Код `td_mebli_mrp` 19.0.1.1.2 так само не копіює статичні плиту й кромку ролі декору — перевірено на цій базі з повернутими рядками старого шаблону (результат той самий). Таблиця нижче — спроба 3 (рядок `11` тоді — 7 / 7).


Спроба 3 (2026-11-13), Odoo 19.0 CE @ `40e9be2b`, мова uk_UA, модулі — `package/addons` @ `4e96a56` (знімок `git archive`), шаблони — робоче дерево `flow/A-12-2-test` (база `4e96a56`); **не odoo-mcp** (у тесті заборонено) — `load()` через `odoo-bin shell`, по файлу з фіксацією; після роботи бази видалені. Редакція: CE; EE — **не перевірено** (бази немає).
- `test-mebli-r3cfg-A` — профіль A: 43 модулі `manifest.yaml` (137 installed) + конфіг-пакет A-12 спроби 3 (2 проходи, read-back) → 28 кроків імпорту;
- `test-mebli-r3cfg-light` — профіль light (42 модулі, без `td_mebli_bas`, 136 installed) + конфіг light за SPEC §11.3 → 25 кроків (без `td/19b`–`21b`);
- `test-mebli-r3cfg-std` — лише 26 стандартних модулів (без жодного `td_*`, 120 installed), без конфігу → 15 стандартних файлів: стандартні шаблони не залежать від модулів A-11.

| Файл | A | light | лише стандартні модулі |
|---|---|---|---|
| `01_product.category.csv` | 8 / 8, помилок 0 | 8 / 8, помилок 0 | 8 / 8, помилок 0 |
| `02_res.partner.csv` | 5 / 5, помилок 0 | 5 / 5, помилок 0 | 5 / 5, помилок 0 |
| `03_product.attribute.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | 2 / 2, помилок 0 |
| `04_product.attribute.value.csv` | 6 / 6, помилок 0 | 6 / 6, помилок 0 | 6 / 6, помилок 0 |
| `05_product.product.csv` | 10 / 10, помилок 0 | 10 / 10, помилок 0 | 10 / 10, помилок 0 |
| `06_product.template.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | 2 / 2, помилок 0 |
| `07_product.template.attribute.line.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | 2 / 2, помилок 0 |
| `08_product.supplierinfo.csv` | 4 / 4, помилок 0 | 4 / 4, помилок 0 | 4 / 4, помилок 0 |
| `09_mrp.workcenter.csv` | 4 / 4, помилок 0 | 4 / 4, помилок 0 | 4 / 4, помилок 0 |
| `10_mrp.bom.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | 2 / 2, помилок 0 |
| `11_mrp.bom.line.csv` | 7 / 7, помилок 0 | 7 / 7, помилок 0 | 7 / 7, помилок 0 |
| `12_mrp.routing.workcenter.csv` | 5 / 5, помилок 0 | 5 / 5, помилок 0 | 5 / 5, помилок 0 |
| `13_hr.employee.csv` | 3 / 3, помилок 0 | 3 / 3, помилок 0 | 3 / 3, помилок 0 |
| `14_maintenance.equipment.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | 2 / 2, помилок 0 |
| `15_product.pricelist.csv` | 1 / 1, помилок 0 | 1 / 1, помилок 0 | 1 / 1, помилок 0 |
| `td/01b_product.category.csv` | 1 / 1, помилок 0 | 1 / 1, помилок 0 | — |
| `td/03b_product.attribute.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | — |
| `td/04b_product.attribute.value.csv` | 6 / 6, помилок 0 | 6 / 6, помилок 0 | — |
| `td/05b_product.product.csv` | 8 / 8, помилок 0 | 8 / 8, помилок 0 | — |
| `td/06b_product.template.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | — |
| `td/12b_mrp.routing.workcenter.csv` | 3 / 3, помилок 0 | 3 / 3, помилок 0 | — |
| `td/14b_maintenance.equipment.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | — |
| `td/16_td.mebli.part.rule.csv` | 2 / 2, помилок 0 | 2 / 2, помилок 0 | — |
| `td/17_td.mebli.accrual.reason.csv` | 3 / 3, помилок 0 | 3 / 3, помилок 0 | — |
| `td/18_td.mebli.import.template.csv` | 1 / 1, помилок 0 | 1 / 1, помилок 0 | — |
| `td/19b_res.partner.csv` | 2 / 2, помилок 0 | — | — |
| `td/20b_product.product.csv` | 2 / 2, помилок 0 | — | — |
| `td/21b_hr.employee.csv` | 2 / 2, помилок 0 | — | — |

Разом: стандартні 15 файлів, 63 рядки, помилок 0 у всіх трьох базах (xmlid `td_md.*` — 76); `td/` 13 файлів, 36 рядків (light — 10 файлів, 30 рядків), помилок і попереджень 0 (xmlid `td_md.*` — 82). Після імпорту в A і light замовлення «Шафа-купе» (параметричний виріб, `td/06b`) для кожного з трьох декорів підтверджується: SO → MO зі специфікацією замовлення (`td_order_bom`, 2 деталі, 4 операції, `consumption = warning` — VP-17), плита й кромка — за декором (`td/04b` → `td/05b` `td_matches_board_id`); фасад FACADE-PAINT: SO → PO (MTO + правило складу «Купити»). Умова оплати замовлення в A — `td_mebli_sale.payment_term_td_furniture` (default покупців, конфіг A-12), у light — порожня (VP-05 = false).

## Зміни версії

| Версія | AC/рядок ALLOCATION | Що змінено в шаблонах |
|---|---|---|
| 1.0 | перший запуск (AC-089, AC-090; `tr/migration.md` §1) | створено 15 стандартних і 4 `td/` шаблони |
| 1.1 | A-13 спроба 2 (повтор після A-11 @ `4e0fdda`; AC-049, AC-076, AC-107, AC-111, AC-039…AC-042) | додано 7 файлів `td/`: `01b` (гарантія категорії), `14b` (верстат ↔ дільниця), `17` (причини нарахувань), `18` (шаблон мапінгу G2), `19b`/`20b`/`21b` (`td_bas_code`); стандартні файли не змінено; трасування, порядок і переліки модулів оновлено; тест-імпорт стандартних і `td/` — у базі профілю A |
| 1.2 | A-13 спроба 3 (повтор за CHECKS.md №7, №27; AC-011, AC-024) | додано `td/03b` (`td_component_role`) і `td/04b` (`td_component_product_id`, `td_edge_thickness`); у `05` / `td/05b` — плита «графіт» і кромка до декорів «дуб», «графіт» (щоб кожне значення декору мало плиту й кромку); з `route_ids` `05`, `06` прибрано «Купити» / «Виробництво» (лишився MTO, решту задає склад); порядок імпорту — 28 кроків; тест-імпорт A, light і база лише зі стандартними модулями |
| 1.3 | A-13 спроба 4 (повтор за CHECKS.md №28; AC-013) | `11`: прибрано статичні рядки плити DSP-18-W і кромки EDGE-PVC-2-W шаблону «Шафа-купе» (7 → 5 рядків); узгодження кроків `td_mebli_migration` — 28 кроків (R3-M-01 закрито); тест-імпорт A (28 кроків) + SO → MO трьох декорів |
