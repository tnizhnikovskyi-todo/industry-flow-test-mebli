# `td_mebli_mrp` — специфікація замовлення, деталі, імпорт, норми, завантаження

**Призначення.** S-03 «Специфікація замовлення» (F-01, F-02, F-27), основа S-01/S-02 (F-03, F-04 — параметричний виріб), S-06 (F-06, F-33), аналоги (F-57, B). Специфікація замовлення — стандартна `mrp.bom` з ознакою; деталь — рядок специфікації `td.mebli.part` (AI-A08-01). Коробка A (аналоги, AI-мапінг — B). AC: AC-011…AC-014, AC-045…AC-052, AC-068, AC-069, AC-088, AC-116.

**Звірка зі стандартом:** `addons/mrp/models/mrp_bom.py:70` (`consumption`), `:89` (`produce_delay`), `:92` (`days_to_prepare_mo`), `:703` (`product_qty` рядка), `:777` (`_skip_bom_line`); `addons/mrp/models/mrp_production.py:160` (`bom_id`), `:786-795` (`_compute_date_finished`); `addons/mrp/models/mrp_routing.py:27,33` (`time_mode`, `time_cycle_manual`); `addons/mrp/models/mrp_workcenter.py:67` (`workcenter_load`), `:81` (`resource_calendar_id`); `addons/mrp/models/mrp_workorder.py:88` (`duration_expected`); `addons/product/models/product_template_attribute_exclusion.py:7`; `addons/product/models/product_attribute_custom_value.py:17` (`custom_value`); `addons/base_import/models/base_import.py:177`. Таблиця «Модель даних» PLAN.md — рядки `td.mebli.part`, `mrp.bom.td_*`, `product.template.td_*`, `mrp.routing.workcenter.td_*`, `mrp.workorder.td_*`.

## 1. Модель «Деталь» (`td.mebli.part`) — зріз

| Назва поля | Тип поля | Звідки тягнути значення | Додаткова примітка |
|---|---|---|---|
| Специфікація (`bom_id`) | many2one `mrp.bom` | генератор / імпорт | required, `ondelete='cascade'`, index |
| Компанія (`company_id`) | many2one `res.company`, related `bom_id.company_id`, store | — | **нове в A-11** (R-03); у специфікації без компанії — компанія замовлення |
| Правило (`rule_id`) | many2one `td.mebli.part.rule` | генератор | порожнє для імпортованих |
| Номер (`sequence`) | integer | — | порядок і номер на етикетці |
| Деталь (`name`) | char | правило / файл | required |
| Матеріал (`material_id`) | many2one `product.product` | правило / файл | required; domain: `td_material_kind = 'board'` |
| Кількість (`qty`) | integer | правило / файл | default 1 |
| Довжина, мм (`length_mm`), Ширина, мм (`width_mm`) | float | правило / файл | `models.Constraint` `CHECK(length_mm > 0 AND width_mm > 0)` — **нове** |
| Кромка довгих / коротких сторін (`edge_long_sides`, `edge_short_sides`) | integer 0–2 | правило / файл | constraint 0–2 |
| Кромка (`edge_product_id`) | many2one `product.product` | правило / файл | domain `td_material_kind = 'edge'` |
| Площа, м² (`area_m2`), Кромка, м (`edge_length_m`) | float compute, store | розміри × кількість | — |
| Відправлено в розкрій (`locked`) | boolean compute, store | є завдання розкрою в стані «відправлено» або закупівля порізки | **нове**; `write`/`unlink` при `locked` — UserError «Специфікацію відправлено в розкрій (версія N) — зміна лише дозамовленням» (AC-052) |

## 2. Правило деталі (`td.mebli.part.rule`) — зріз
Поля зрізу без змін (`product_tmpl_id`, `name`, `qty`, `material_role`, `fixed_material_id`, коефіцієнти `len_*`, `wid_*` і константи, кромка сторін). Формула: довжина = `len_w`·Ш + `len_h`·В + `len_d`·Г + `len_const` (так само ширина). Довідник — меню «Виробництво → Налаштування → Правила деталей» (група `group_technologist`).

## 3. Розширення `mrp.bom` — зріз
`td_order_bom` (boolean, ставить система), `td_template_bom_id` (m2o `mrp.bom`), `td_width`/`td_height`/`td_depth` (integer, ставить система), `td_part_ids` (o2m `td.mebli.part`), підсумки `td_part_count`, `td_board_area_m2`, `td_edge_length_m` (compute). **Нове в A-11:** `td_version` (integer, readonly, +1 при кожному відправленні в розкрій; показується на завданні розкрою й етикетках, AC-028). Генератор специфікації замовлення копіює `produce_delay`, `days_to_prepare_mo` шаблону і ставить `consumption = 'warning'` (AC-116; стандарт `mrp_bom.py:70`). Рядки плити й кромки (`mrp.bom.line.td_from_parts`, compute без store) — перерахунок з деталей: площа × (1 + `td_waste_pct`/100), довжина кромки.

## 4. Розширення `product.template` / атрибутів — зріз
`td_is_parametric`, номінальні й граничні розміри `td_*_nominal/min/max` (integer), `td_edge_allowance_mm`, `td_part_rule_ids`, `td_material_kind` (selection: плита / кромка / фурнітура / готовий фасад; + «Послуга порізки» з `td_mebli_cutting`), `td_sheet_length_mm`, `td_sheet_width_mm`, `td_thickness_mm`, `td_waste_pct`, `td_matches_board_id`, `td_edge_thickness`; `product.attribute.td_dimension`, `td_component_role`; `product.attribute.value.td_component_product_id`, `td_edge_thickness`. **Нове в A-11:** `models.Constraint` `td_width_min <= td_width_max` (і для висоти, глибини); перевірка розмірів рядка (`sale.order.line` у `td_mebli_sale`): «Ширина N мм поза межами виробу (min–max мм)» (AC-012).

**Сумісність опцій (F-03) — конфіг:** стандартні виключення значень атрибутів `product.template.attribute.exclusion` (`addons/product/models/product_template_attribute_exclusion.py:7`) — дані конфіг-пакета/A-13 (AC-011); власної моделі правил сумісності немає. Меню конфігуратора — `group_feature_configurator`.

## 5. Норми й розцінки операцій — зріз
`mrp.routing.workcenter.td_time_basis` (selection: на деталь / на м кромки / на м² плити / на операцію), `td_time_rate` (float, хв на одиницю бази), `td_piece_rate` (monetary, `currency_field='td_currency_id'`, `groups` — §4 `security.md`), `td_currency_id` (compute). Генератор пише `time_cycle_manual` специфікації замовлення = `td_time_rate` × кількість бази (AC-068).

## 6. Завантаження дільниць — зріз
`mrp.workcenter.td_capacity_hours` (float compute, без store: `resource_calendar_id.hours_per_week` × паралельність), `mrp.workorder.td_expected_hours`, `td_load_pct`, `td_load_stage`, `td_load_zone` (compute). Подання: `<list>`, `<pivot>` і `<graph>` за дільницею й тижнем `date_start` (`interval="week"`), `<calendar date_start="date_start">`; Ганта немає (`odoo/addons/base/models/ir_ui_view.py:149-153`) — AC-069.

## 7. Показ деталей у МО й планшеті — зріз
`mrp.production.td_part_ids` (related `bom_id.td_part_ids`, readonly), `td_part_count`, `td_board_area_m2`, `td_edge_length_m`; `mrp.workorder.td_part_ids`, `td_part_count` (related); `stock.move.td_from_parts` (compute). Вкладка «Деталі» МО, кнопка «Деталі» на планшеті.

## 8. Майстер імпорту специфікації (`td.mebli.spec.import`, TransientModel) — зріз + доробки

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Специфікація (`bom_id`) | many2one `mrp.bom` | контекст | required |
| Файл (`file`), Ім'я файлу (`filename`) | binary, char | користувач | `.csv`, `.xlsx` (читання xlsx — бібліотека `openpyxl`, як стандартний `base_import`) |
| Розпізнані колонки (`mapping`) | text, readonly | словник синонімів → шаблон → AI (B) | — |
| Деталей у файлі (`preview_count`) | integer, readonly | — | — |
| **Режим (`mode`)** | selection: `replace` «Замінити деталі» / `append` «Додати до наявних»; default `replace` | користувач | **нове** (R-10, AC-045) |
| **Шаблон мапінгу (`template_id`)** | many2one `td.mebli.import.template` | автопідбір за заголовками | **нове** (AC-049) |
| **Невідомі рядки (`unknown_lines`)** | text, readonly | перевірка матеріалів | **нове**; не порожнє → кнопка «Імпортувати» недоступна (`invisible="unknown_lines"`) (AC-047) |

**Бізнес-правила.**
1. Обов'язкові колонки: деталь, довжина, ширина, кількість, матеріал; відсутні → UserError «У файлі не знайдено колонок: <перелік>. Перевірте заголовки або задайте мапінг» (AC-046).
2. `replace` видаляє деталі специфікації без `locked`; при `locked` — UserError AC-052.
3. Після запису — перерахунок рядків плити й кромки з деталей (`_td_prepare_component_lines`) і повідомлення в чаті: файл, кількість, режим.
4. Ціль продуктивності — 300 деталей ≤ 30 с (пакетне `create` списком, AC-048).
5. AI-підказка (B, `group_feature_ai_mapping`): назовні — заголовки й ≤ 10 рядків (лише розміри й назви матеріалів); постачальник моделі — не обрано (AI-A08-13).

## 9. Шаблон мапінгу (`td.mebli.import.template`) — новий

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Назва (`name`) | char | технолог | напр. «PRO100 салону» |
| Компанія (`company_id`) | many2one `res.company` | поточна | правило multi-company |
| Підпис заголовків (`header_signature`) | char, index | нормалізовані заголовки файлу | пошук шаблону |
| Мапінг (`mapping_json`) | json (`odoo/orm/fields_misc.py:55`) | технолог | колонка файлу → поле деталі |
| Активний (`active`) | boolean | — | — |

## 10. Аналоги (F-57, B) — хвиля 2
`product.template.td_analog_ids` (many2many `product.product`), `stock.move.td_analog_id` (m2o compute: перший аналог з вільним залишком), `td_analog_hint` (char compute). Кнопка «Взяти аналог» на рядку компонента МО (`invisible="not td_analog_id"`, група `group_feature_analog`): замінює `product_id` руху, запис у чаті МО (AC-088).

## 11. UI/UX
- Меню: «Виробництво → Специфікації замовлень» (фільтр `td_order_bom`), «Виробництво → Налаштування → Правила деталей», «… → Шаблони імпорту».
- Форма специфікації замовлення: шапка — виріб, розміри, версія; вкладки «Деталі» (`<list editable="bottom">`: №, деталь, матеріал, Д×Ш, к-сть, кромка, площа), «Компоненти» (позначка «З деталей»), «Операції»; кнопки «Імпорт деталей» (`invisible="locked"`), «Друкувати етикетки».
