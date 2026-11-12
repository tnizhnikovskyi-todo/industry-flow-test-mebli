# `td_mebli_shop` — кіоск цеху, крок якості, комплектувальний лист, етикетки

**Призначення.** S-06 (F-32, F-34, F-18 варіант 12 — коробка B), S-16 (F-37, F-29, друк F-49 — коробка A). AC: AC-061, AC-062, AC-071…AC-075, AC-091…AC-094.
**Звірка:** `addons/mrp/models/mrp_workorder.py:667` (`button_start`), `:716` (`button_finish`), `:764` (`button_pending`), `:118` (`time_ids`); `addons/mrp/models/mrp_workcenter.py:477` (`mrp.workcenter.productivity.loss`), `:531` (`productivity.user_id`), `:594-605` (розщеплення таймера `copy()`); `addons/hr/models/hr_employee.py:211` (`pin`); `addons/hr_attendance/controllers/main.py:139`, `:203-208` (взірець перевірки PIN); `addons/stock/models/stock_picking.py:1450` (`button_validate`); `quality_control` — лише EE (`odoo/addons/base/data/ir_module_module.xml:131`); `stock_barcode` — лише EE (заглушка). PLAN.md: `td.mebli.kiosk`, `td.mebli.quality.check`, `td.mebli.kit.line`, `mrp.workcenter.productivity.td_employee_id`, `mrp.workorder.td_quality_*`.

## 1. Кіоск за PIN (F-32, B) — зріз + доробки
**`td.mebli.kiosk`** (TransientModel): `workorder_id` (m2o, required), `action` (selection: «Взято» / «Пауза» / «Зроблено» / **«Брак»** — нове), `employee_id` (m2o `hr.employee`, required, domain — працівники компанії завдання), `company_id` (related), `pin` (char), `loss_id` (m2o `mrp.workcenter.productivity.loss`, required якщо `action == 'pause'`), `quality_point`, `result`, `photo`, `note` (крок якості), **`scrap_part_id`** (m2o `td.mebli.part`, для «Брак»), **`scrap_reason`** (char).

**Бізнес-правила.**
1. PIN перевіряється з правами системи лише на рівність; невдала спроба +1 до `hr.employee.td_pin_fail_count`; 5 поспіль → `td_pin_locked_until = now + 15 хв`; повідомлення «Невірний PIN» / «Працівника заблоковано до HH:MM» (AC-071; AI-A08-12, R-11).
2. «Взято»: стандартний `button_start` від користувача-планшета; відкритий рядок `mrp.workcenter.productivity` отримує `td_employee_id`. Якщо на завданні вже відкритий рядок іншого працівника з цього планшета — UserError «Завдання вже виконує <А>…» (AC-072).
3. «Пауза» закриває рядок цього працівника з причиною втрат (`loss_id`), «Зроблено» — `button_finish`; якщо операція має крок якості без перевірки — UserError «Пройдіть крок якості: <назва>» (AC-075).
4. «Брак» (умовно, після A-06; `group_feature_kiosk`): створює МО на деталь (походження — завдання, причина), запис у журналі невідповідностей (AC-073).
5. `mrp.workcenter.productivity.copy()` переносить `td_employee_id` (розщеплення таймера стандартом).

**Розширення:** `mrp.workcenter.productivity.td_employee_id` (m2o `hr.employee`, ставить система); `mrp.workorder.td_worker_names`, `td_pause_reason` (char compute, лише відкриті рядки); `hr.employee.td_pin_fail_count` (integer), `td_pin_locked_until` (datetime) — **нові**, `groups='hr.group_hr_user'`.

## 2. Крок якості з фото (F-34, B) — зріз
`mrp.routing.workcenter.td_quality_point` (char — назва кроку), `mrp.workorder.td_quality_point` (related), `td_quality_ids` (o2m), `td_quality_state` (selection compute: немає / очікує / пройдено / не пройдено).
**`td.mebli.quality.check`:** `workorder_id` (required, cascade), `production_id`, `workcenter_id` (related, store), `name` (required), `result` (selection pass/fail, required), `photo` (image 1024), `note`, `employee_id` (readonly), **`company_id`** (related `workorder_id.company_id`, store — нове, R-03). Створення — лише через кіоск (права `create` у групи кіоску; майстер — читання й запис). «Не пройдено» → показник 12 дашборда.

## 3. Комплектувальний лист (F-37, A) — зріз + доробки
**`td.mebli.kit.line`**

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Замовлення (`order_id`) | many2one `sale.order` | генерація листа | required, cascade |
| Компанія (`company_id`) | related `order_id.company_id`, store | — | **нове** (R-03) |
| Місце (`place`) | integer | комплектувальник | required, default 1 |
| Вид (`kind`) | selection: корпус / фасади / фурнітура / інше | генерація | — |
| Позиція (`item`), Деталь (`part_id`), Кількість (`qty`) | char / m2o `td.mebli.part` / float | деталі специфікацій і фурнітура МО | — |
| Етикетка (`label`) | char compute | код `<замовлення>-<МО>-<№ деталі>` | той самий код у QR (AC-061) |
| Запаковано (`packed`), Запакував (`packed_by_id`) | boolean / m2o `res.users`, readonly | кнопка / сканування | `packed_by_id` пише поточний користувач (не система — README зрізу §9) |
| **Дозамовлено (`reorder_production_id`)** | m2o `mrp.production`, readonly | кнопка «Створити дозамовлення» | **нове** (AC-093) |

`sale.order.td_kit_line_ids`, `td_kit_missing`, `td_kit_places` (compute) — смарт-кнопка «Не запаковано». `stock.picking.button_validate` (успадкування): для відвантаження замовлення з незапакованими рядками — UserError «Комплект неповний: не запаковано <перелік>» (AC-092).

## 4. Етикетки (F-29) — хвиля 2
`ir.actions.report` QWeb-PDF «Етикетки деталей» на `mrp.production` і `sale.order`: на кожну деталь × кількість — назва, Д×Ш, матеріал, замовлення, місце, QR (стандартний генератор штрихкодів звітів: маршрут `/report/barcode` — `addons/web/controllers/report.py:56`, `ir.actions.report.barcode` — `odoo/addons/base/models/ir_actions_report.py:688`, тип `QR`). Формат паперу — `report.paperformat` 58×40 мм (дані модуля; принтер клієнта — ризик R-1). Сканування (B, `group_feature_label_scan`): поле сканування на формі листа (віджет `barcode_handler` модуля CE `barcodes` — `addons/barcodes/static/src/barcode_handler_field.js:23`; залежність `barcodes` додається в `td_mebli_shop`; робота з камерою телефона — ризик, перевіряє пілот; запасний шлях — поле вводу коду з Enter) знаходить рядок за `label`; чужий код — повідомлення AC-062.

## 5. UI/UX
Меню «Виробництво → Планшет цеху» (група `group_kiosk` і майстер): `<list>` робочих завдань дільниці на зміну з кнопками «Взято / Пауза / Зроблено / Деталі», на телефоні — `<kanban>`. Меню «Склад → Комплектація» — `<list editable>` листа за місцями, кнопки «Друкувати», «Створити дозамовлення» (`invisible="packed or reorder_production_id"`).
