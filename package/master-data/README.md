# Шаблони майстер-даних пакета mebli (версія 1.0, перший запуск A-13)

База коду: SHA `351d4a8` (гілка `flow/A-12-test`) | ТР: `package/SPEC.md`@`351d4a8`, `package/tr/migration.md` §1@`351d4a8` | ALLOCATION: `package/ALLOCATION.md`@`351d4a8` | CONFIG: `package/config/CONFIG.md` (A-12, та сама гілка, не закомічено на момент A-13) | BOX: `docs/industries/mebli/research/BOX.md` §3–4@`351d4a8`

Скіл: `flow-package-build:master-data-template-builder (версія 0.3.1)`. Формат — `master-data-format.md` (UTF-8, `,`, перший стовпець `id` = `td_md.<model_slug>_<slug>`, many2one / many2many — `<поле>/id`). Усі приклади **вигадані** (контрагенти «Демо-…», без ПІБ, телефонів, email, ЄДРПОУ, IBAN); кількості — ілюстративні; **ціни, норми часу, години й суми — порожні** (заповнює клієнт у B-06; правило тесту «без годин і грошей»).

## Файли

| Файл | Модель | Рядків | Призначення (розділ/AC ТР) |
|---|---|---|---|
| `01_product.category.csv` | `product.category` | 8 | `tr/migration.md` §1 №3; категорії номенклатури (BOX §3) |
| `02_res.partner.csv` | `res.partner` | 5 | №6, №17; постачальники плит, фурнітури, фасадів, порізки (AC-024, AC-085, AC-026); покупець-компанія |
| `03_product.attribute.csv` | `product.attribute` | 2 | №7; декор і кромка для конфігуратора (AC-011, коробка B) |
| `04_product.attribute.value.csv` | `product.attribute.value` | 6 | №7; значення декору й кромки |
| `05_product.product.csv` | `product.product` | 7 | №4, №5; плити, кромка, фурнітура, замовний фасад (MTO + «Купити», AC-024) |
| `06_product.template.csv` | `product.template` | 2 | №7; вироби «Шафа-купе», «Тумба» (маршрути «Виробництво» + MTO) |
| `07_product.template.attribute.line.csv` | `product.template.attribute.line` | 2 | №7; атрибути виробу (AC-011) |
| `08_product.supplierinfo.csv` | `product.supplierinfo` | 4 | №6; ціни й строки постачальників (AC-024, AC-085) |
| `09_mrp.workcenter.csv` | `mrp.workcenter` | 4 | №9; дільниці розкрій, кромкування, присадка, збирання |
| `10_mrp.bom.csv` | `mrp.bom` | 2 | №9; шаблони специфікацій виробів |
| `11_mrp.bom.line.csv` | `mrp.bom.line` | 7 | №9; компоненти специфікацій |
| `12_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` | 5 | №9; операції маршруту (норми часу — порожньо) |
| `13_hr.employee.csv` | `hr.employee` | 3 | №12; працівники (PIN кіоску, AC-077 — порожньо, задає клієнт) |
| `14_maintenance.equipment.csv` | `maintenance.equipment` | 2 | №11; обладнання (зв'язок з дільницею — `td_mebli_maint`, A-11) |
| `15_product.pricelist.csv` | `product.pricelist` | 1 | BOX §3 «Прайс-листи й валюта (EUR для фурнітури)» |
| `td/05b_product.product.csv` | `product.product` (поля `td_*`) | 5 | №4; вид матеріалу, формат листа, товщина, % відходу, кромка ↔ плита |
| `td/06b_product.template.csv` | `product.template` (поля `td_*`) | 2 | №7; параметричний виріб, розміри й межі |
| `td/12b_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` (поля `td_*`) | 3 | №9; база норми, норма, розцінка (порожньо), контрольна точка |
| `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | 2 | №8; правила деталей виробу |

## Порядок імпорту

Джерело-перелік (вимога): `package/config/CONFIG.md` «Модулі до установки», профіль `ce` / коробка A (`manifest.yaml`, без `when:`): `base_setup, mail, calendar, portal, hr, crm, stock, mrp, project, account, sale_crm, sale_margin, sale_stock, sale_mrp, sale_project, purchase, purchase_stock, sale_purchase_stock, purchase_mrp, mrp_account, repair, l10n_ua, hr_attendance, hr_hourly_cost, maintenance, base_import, td_mebli_base, td_mebli_mrp, td_mebli_sale, td_mebli_measure, td_mebli_cutting, td_mebli_purchase, td_mebli_ua, td_mebli_shop, td_mebli_install, td_mebli_claim, td_mebli_cost, td_mebli_maint, td_mebli_attendance, td_mebli_migration, td_mebli_dashboard, td_mebli_notify` (+ `td_mebli_bas` при VP-04 = `true`).

Фактично installed у тестовій базі `test-mebli-a13md` (131 модуль; повний список): `account, account_add_gln, account_edi_ubl_cii, account_payment, analytic, api_doc, auth_passkey, auth_passkey_portal, auth_signup, auth_totp, auth_totp_mail, auth_totp_portal, barcodes, barcodes_gs1_nomenclature, base, base_geolocalize, base_import, base_import_module, base_install_request, base_setup, bus, calendar, calendar_sms, contacts, crm, crm_iap_enrich, crm_iap_mine, crm_sms, digest, google_gmail, hr, hr_attendance, hr_calendar, hr_homeworking, hr_homeworking_calendar, hr_hourly_cost, hr_maintenance, hr_org_chart, hr_skills, html_editor, http_routing, iap, iap_crm, iap_mail, l10n_ua, mail, mail_bot, mail_bot_hr, maintenance, microsoft_outlook, mrp, mrp_account, mrp_repair, onboarding, partner_autocomplete, payment, phone_validation, portal, portal_rating, privacy_lookup, product, project, project_account, project_hr_skills, project_mrp, project_mrp_account, project_mrp_sale, project_purchase, project_purchase_stock, project_sms, project_stock, project_stock_account, project_todo, purchase, purchase_edi_ubl_bis3, purchase_mrp, purchase_repair, purchase_stock, rating, repair, resource, resource_mail, rpc, sale, sale_crm, sale_edi_ubl, sale_management, sale_margin, sale_mrp, sale_pdf_quote_builder, sale_project, sale_project_stock, sale_project_stock_account, sale_purchase, sale_purchase_project, sale_purchase_stock, sale_service, sale_sms, sale_stock, sale_stock_margin, sales_team, sms, snailmail, snailmail_account, spreadsheet, spreadsheet_account, spreadsheet_dashboard, spreadsheet_dashboard_account, spreadsheet_dashboard_sale, spreadsheet_dashboard_stock_account, stock, stock_account, stock_maintenance, stock_sms, td_mebli_claim, td_mebli_cost, td_mebli_cutting, td_mebli_dashboard, td_mebli_install, td_mebli_measure, td_mebli_mrp, td_mebli_purchase, td_mebli_sale, td_mebli_shop, td_mebli_ua, uom, utm, web, web_hierarchy, web_tour, web_unsplash`.

Перевірка MD-modules: усі 26 стандартних модулів джерела ⊆ installed; **6 модулів `td_*` джерела відсутні** (`td_mebli_base`, `td_mebli_maint`, `td_mebli_attendance`, `td_mebli_migration`, `td_mebli_notify`; `td_mebli_bas` у профілі A) — їх немає в `package/addons` гілки кроку (дефект для A-11). Стандартні шаблони від них не залежать — імпортовано (рішення AI-A13-02).

| NN | Файл | Модель | Залежить від | Рядків | Модулі |
|---|---|---|---|---|---|
| 01 | `01_product.category.csv` | `product.category` | — (батьки — вище в тому ж файлі) | 8 | product |
| 02 | `02_res.partner.csv` | `res.partner` | — | 5 | base (+ `supplier_rank`/`customer_rank`: account, purchase) |
| 03 | `03_product.attribute.csv` | `product.attribute` | — | 2 | product |
| 04 | `04_product.attribute.value.csv` | `product.attribute.value` | 03 | 6 | product |
| 05 | `05_product.product.csv` | `product.product` | 01; xmlid `uom.*`, `stock.route_warehouse0_mto`, `purchase_stock.route_warehouse0_buy` | 7 | product, stock, purchase_stock |
| 06 | `06_product.template.csv` | `product.template` | 01; xmlid `uom.product_uom_unit`, `mrp.route_warehouse0_manufacture`, `stock.route_warehouse0_mto` | 2 | product, stock, mrp |
| 07 | `07_product.template.attribute.line.csv` | `product.template.attribute.line` | 03, 04, 06 | 2 | product |
| 08 | `08_product.supplierinfo.csv` | `product.supplierinfo` | 02, 05 | 4 | product, purchase |
| 09 | `09_mrp.workcenter.csv` | `mrp.workcenter` | — | 4 | mrp |
| 10 | `10_mrp.bom.csv` | `mrp.bom` | 06 | 2 | mrp |
| 11 | `11_mrp.bom.line.csv` | `mrp.bom.line` | 05, 10 | 7 | mrp |
| 12 | `12_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` | 09, 10 | 5 | mrp |
| 13 | `13_hr.employee.csv` | `hr.employee` | — | 3 | hr (`pin` — hr_attendance) |
| 14 | `14_maintenance.equipment.csv` | `maintenance.equipment` | — | 2 | maintenance |
| 15 | `15_product.pricelist.csv` | `product.pricelist` | xmlid `base.EUR` | 1 | product |
| td 05b | `td/05b_product.product.csv` | `product.product` (`td_*`) | 05 (другий прохід тих самих `id`) | 5 | td_mebli_mrp |
| td 06b | `td/06b_product.template.csv` | `product.template` (`td_*`) | 06 | 2 | td_mebli_mrp |
| td 12b | `td/12b_mrp.routing.workcenter.csv` | `mrp.routing.workcenter` (`td_*`) | 12 | 3 | td_mebli_mrp, td_mebli_shop |
| td 16 | `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | 06 | 2 | td_mebli_mrp |

Стандартні записи, на які посилаються шаблони (звірено в `ir.model.data` тестової бази): `uom.product_uom_square_meter` (м²), `uom.product_uom_meter` (м), `uom.product_uom_unit` (штуки), `stock.route_warehouse0_mto` (у чистій базі архівний; активує конфіг-пакет A-12, `td_config.route_mto_active`), `purchase_stock.route_warehouse0_buy`, `mrp.route_warehouse0_manufacture`, `base.EUR` (валюту активує клієнт/B-04).

## Залежності між файлами

- `04` → `03`: `attribute_id/id`; `07` → `03`, `04`, `06`: `attribute_id/id`, `value_ids/id`, `product_tmpl_id/id`.
- `05`, `06` → `01`: `categ_id/id`; `08` → `02`, `05`: `partner_id/id`, `product_id/id` (`product_tmpl_id` обчислюється з варіанта).
- `10` → `06`: `product_tmpl_id/id`; `11` → `10`, `05`: `bom_id/id`, `product_id/id` (компоненти — лише з `05`, бо `product.template` з `06` не дає xmlid варіанту); `12` → `09`, `10`.
- Двопрохідні: `td/05b`, `td/06b`, `td/12b` — другий прохід тих самих `id` з полями `td_*` (після `05`, `06`, `12`); `td/16` → `06`. Циклів немає.

## Трасування ТР -> шаблон

| Довідник/поле ТР (розділ, AC) | Модель Odoo | Трек ALLOCATION | Файл або позначка |
|---|---|---|---|
| №1 Компанії й параметри (`td_*` на компанії) | `res.company` | конфіг (VP, A-12) | `конфіг (A-12)` — `package/config/` (`td_config.param_*`, `td_config.company_*`) |
| №2 Одиниці: лист, м², п. м, шт, комплект | `uom.uom` | конфіг (BOX §3 «в коробці») | `конфіг (A-12)`; м², м, шт — стандартні xmlid; «лист», «комплект» — **Відкрите питання**: у конфіг-пакеті A-12 їх немає (немає AC в ALLOCATION) |
| №3 Категорії товарів | `product.category` | стандарт (майстер-дані, BOX §3) | `01_product.category.csv` |
| №3 Гарантія на категорію (`td_warranty_months`) | `product.category` | код (A-11) | `потребує модулів A-11` — поля немає в гілці; шаблон після появи (порожньо до юриста, рішення №17) |
| №4 Плити, кромка, фурнітура | `product.product` | стандарт | `05_product.product.csv` |
| №4 Поля матеріалу `td_*` | `product.product` | код (`td_mebli_mrp`) | `td/05b_product.product.csv`; `td_bas_code` — поля немає (`td_mebli_bas`, A-11) |
| №5 Замовні позиції (MTO + «Купити», AC-024) | `product.product` | конфіг (маршрут — A-12) + стандарт (товар) | `05_product.product.csv` (рядок `FACADE-PAINT`) |
| №6 Ціни постачальників (AC-085) | `product.supplierinfo` | стандарт | `08_product.supplierinfo.csv` |
| №7 Вироби, атрибути (AC-011) | `product.template`, `product.attribute(.value)`, `product.template.attribute.line` | конфіг AC-011 (налаштування варіантів — A-12) + майстер-дані | `03`, `04`, `06`, `07` |
| №7 Виключення сумісності (AC-011, B) | `product.template.attribute.exclusion` | конфіг | **Відкрите питання**: рядки посилаються на `product.template.attribute.value` без стабільного xmlid — задаються на формі виробу (B-04) |
| №7 Розміри параметричного виробу | `product.template` (`td_*`) | код (`td_mebli_mrp`) | `td/06b_product.template.csv` |
| №8 Правила деталей | `td.mebli.part.rule` | код | `td/16_td.mebli.part.rule.csv` |
| №9 Дільниці, операції, специфікації | `mrp.workcenter`, `mrp.bom`, `mrp.bom.line`, `mrp.routing.workcenter` | стандарт | `09`, `10`, `11`, `12` |
| №9 Норми й розцінки (`td_time_*`, `td_piece_rate`, `td_quality_point`) | `mrp.routing.workcenter` (`td_*`) | код | `td/12b_mrp.routing.workcenter.csv` |
| №9 Потужність дільниці (`td_capacity_hours`) | `mrp.workcenter` (`td_*`) | код | `потребує модулів A-11` — у шаблон не винесено (години — без значень у тесті); Відкрите питання |
| №10 Причини втрат | `mrp.workcenter.productivity.loss` | конфіг | `конфіг (A-12)` — `td_config.loss_*` |
| №11 Обладнання ↔ дільниці | `maintenance.equipment` (+ `td_workcenter_id`) | стандарт + код | `14_maintenance.equipment.csv`; `td_workcenter_id` — модуля `td_mebli_maint` немає (A-11) |
| №12 Працівники, PIN, бригади | `hr.employee` | стандарт (AC-077) | `13_hr.employee.csv`; бригада й `td_bas_code` — `потребує модулів A-11` |
| №13 Умови оплати з етапами | `account.payment.term` / `.line` (`td_milestone`) | конфіг (VP-05) | `конфіг (A-12)` — `td_config.payment_term_stages` |
| №14 Причини премій і штрафів | `td.mebli.accrual.reason` | код | `потребує модулів A-11` — моделі немає в гілці (є лише `td.mebli.accrual`) |
| №15 Теги рекламацій | `repair.tags` | конфіг (`tr/migration.md`) | `конфіг (A-12)` — **Відкрите питання**: у конфіг-пакеті A-12 немає (немає AC в ALLOCATION) |
| №16 Шаблони мапінгу імпорту | `td.mebli.import.template` | код (`td_mebli_migration`) | `потребує модулів A-11` — моделі немає в гілці |
| №17 Клієнти | `res.partner` | стандарт (B-06) | `02_res.partner.csv` (рядок покупця-компанії) |
| BOX §3 Прайс-листи (EUR) | `product.pricelist` | стандарт | `15_product.pricelist.csv` |
| AC-089, AC-090 Міграція (ALLOCATION: A-11 + A-13 шаблони) | ці шаблони | код + A-13 | усі файли вище; конвертори й звірка — `td_mebli_migration` (A-11) |

## Потребують модулів A-11

| Файл `td/` | Модель/поле td_* | Модуль A-11 | Хто перевіряє імпорт |
|---|---|---|---|
| `td/05b_product.product.csv` | `td_material_kind`, `td_sheet_length_mm`, `td_sheet_width_mm`, `td_thickness_mm`, `td_waste_pct`, `td_edge_thickness`, `td_matches_board_id` | `td_mebli_mrp` | A-14 (track-convergence) / A-15 |
| `td/06b_product.template.csv` | `td_is_parametric`, `td_*_nominal`, `td_*_min`, `td_*_max`, `td_edge_allowance_mm` | `td_mebli_mrp` | A-14 / A-15 |
| `td/12b_mrp.routing.workcenter.csv` | `td_time_basis`, `td_time_rate`, `td_piece_rate`, `td_quality_point` | `td_mebli_mrp`, `td_mebli_shop` | A-14 / A-15 |
| `td/16_td.mebli.part.rule.csv` | `td.mebli.part.rule` | `td_mebli_mrp` | A-14 / A-15 |
| — (шаблону ще немає) | `td_warranty_months`, `td_bas_code`, `td_workcenter_id`, бригада, `td.mebli.accrual.reason`, `td.mebli.import.template`, `td_capacity_hours` | `td_mebli_base`, `td_mebli_bas`, `td_mebli_maint`, `td_mebli_migration`, `td_mebli_shop` | після появи полів у A-11 — повтор A-13 |

Ці шаблони не проходять тест-імпорт в A-13: імпорт перевіряє A-14 після злиття A-11 або A-15. Колонки `td/` звірено з `fields_get` тестової бази (модулі зрізу встановлені), значення selection — з бази.

## Тест-імпорт

База: `test-mebli-a13md` — локальна чиста тестова база (Odoo 19.0 CE @ `40e9be2b`, мова uk_UA, модулі профілю A з `manifest.yaml`, 2026-11-13; **не odoo-mcp** — у тесті заборонено; після імпорту видалена) | SHA шаблонів: робоче дерево на базі `351d4a8` (не закомічено на момент імпорту) | Спосіб: `load` (спосіб 2 `test-import.md`) через `odoo-bin shell`, файл за файлом у порядку NN, `xmlid td_md.*` до імпорту — 0 | Редакція: CE; EE — **не перевірено** (доступу немає), шаблони — лише стандартні моделі, спільні для CE і EE

| Файл | Імпортовано | Помилки (`messages`) |
|---|---|---|
| `01_product.category.csv` | 8 / 8 | 0 |
| `02_res.partner.csv` | 5 / 5 | 0 |
| `03_product.attribute.csv` | 2 / 2 | 0 |
| `04_product.attribute.value.csv` | 6 / 6 | 0 |
| `05_product.product.csv` | 7 / 7 | 0 |
| `06_product.template.csv` | 2 / 2 | 0 |
| `07_product.template.attribute.line.csv` | 2 / 2 | 0 |
| `08_product.supplierinfo.csv` | 4 / 4 | 0 |
| `09_mrp.workcenter.csv` | 4 / 4 | 0 |
| `10_mrp.bom.csv` | 2 / 2 | 0 |
| `11_mrp.bom.line.csv` | 7 / 7 | 0 |
| `12_mrp.routing.workcenter.csv` | 5 / 5 | 0 |
| `13_hr.employee.csv` | 3 / 3 | 0 |
| `14_maintenance.equipment.csv` | 2 / 2 | 0 |
| `15_product.pricelist.csv` | 1 / 1 | 0 |

Разом 59 рядків, 70 xmlid `td_md.*`, помилок 0. Перевірено після імпорту: маршрути MTO + «Купити» у фасаду, «Виробництво» + MTO у виробу (зв'язки збережено; MTO архівний до конфігу A-12), специфікація шафи — 4 компоненти й 4 операції, `product_tmpl_id` постачальника обчислено з варіанта.

## Зміни версії

| Версія | AC/рядок ALLOCATION | Що змінено в шаблонах |
|---|---|---|
| 1.0 | перший запуск (AC-089, AC-090; `tr/migration.md` §1) | створено 15 стандартних і 4 `td/` шаблони |
