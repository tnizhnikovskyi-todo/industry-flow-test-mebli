# `td_mebli_sale` — замовлення клієнта: дати, прогноз, графік оплат, договір, ціна з розмірів, зміни

**Призначення.** S-02 «Замовлення клієнта», S-05 «Дошка замовлень» (етап до «Виготовлено»), S-18 «Погодження й зміна». F-04, F-07, F-09, F-21–F-24, F-31, F-36, F-44, F-49 (договір), F-53, F-63. Коробка A (підпис зміни — B). AC: AC-013…AC-019, AC-022…AC-025, AC-032…AC-034, AC-063, AC-064, AC-066, AC-067, AC-083, AC-118…AC-120.

**Звірка зі стандартом:** `addons/sale/models/sale_order.py:61` (`company_id`), `:71` (`state`), `:88` (`commitment_date`), `:112` (`require_signature`), `:240` (`invoice_ids`); `addons/sale_margin/models/sale_order.py:10-11` (`margin`, `margin_percent`); `addons/sale_mrp/models/sale_order.py:14` (`mrp_production_ids`); `addons/sale_purchase/models/sale_order.py:54` + `addons/sale_purchase_stock/models/sale_order.py:14` (`_get_purchase_orders`); `addons/purchase/models/purchase_order_line.py:25` (`date_planned`), `:72` (`qty_received`); `addons/purchase_stock/models/purchase_order.py:34` (`on_time_rate`); `addons/account/models/account_payment_term.py:281-308` (рядок умов оплати: `value`, `value_amount`, `nb_days`); `addons/stock/data/stock_data.xml:42` (MTO), `addons/purchase_stock/data/purchase_stock_data.xml:10` («Купити»). PLAN.md «Модель даних»: зразок S-02, «Решта пакета», «Доробка коробки A».

## 1. Дати й прогноз (S-02, S-05) — зріз

Усі поля — compute, без вводу (ввід дат лише в стандартних документах: МО, закупівля).

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Обіцяна дата | стандарт `commitment_date` | менеджер | лише переміщено у формі (`position="move"`) |
| Готовність цеху (`td_shop_date`) | date compute | кінець МО (`_compute_date_finished`) або сьогодні + `produce_delay` шаблону (без МО) | AC-023 |
| Прогнозна дата (`td_forecast_date`) | date compute, store (для дошки й фільтрів) | max(`td_shop_date`, готовність позицій `purchase.order.line.td_date_ready`, повернення порізки) | AC-022 |
| Зсув, днів (`td_delay_days`) | integer compute | прогноз − обіцяна | 0 без обіцяної дати |
| Позиція, що зсуває (`td_late_line_id`, `td_late_item`) | m2o `purchase.order.line` / char compute | — | `groups` продавець і закупівельник |
| Причина зсуву (`td_delay_reason`) | selection compute: `company` «Компанія» / `supplier` «Постачальник» / `cutting` «Порізка в дистриб'ютора» (`selection_add` з `td_mebli_cutting`) / `customer` «Клієнт» | з дат джерел; «Клієнт» — з відкритої/останньої зміни з причиною клієнта | **«Клієнт» — нове в A-11** (AC-066) |
| Закупівлі під замовлення (`td_purchase_line_ids`) | many2many compute | `_get_purchase_orders().order_line`, що живлять МО замовлення | лише читання |
| `purchase.order.line.td_date_ready` | date compute | `date_planned` + запізнення постачальника + `produce_delay` специфікації МО-споживача | — |
| `purchase.order.line.td_supplier_delay` | integer compute | `res.partner.td_supplier_delay_avg` | хвиля 2, F-63 |
| `res.partner.td_supplier_delay_avg` (Запізнення за історією, днів), `td_supplier_delay_lines` | float / integer compute | отримані рядки закупівель: дата приймання − `date_planned` | поряд — стандартний `on_time_rate`; без історії — 0 і «немає історії» (AC-025) |

**Затримані поставки (F-09, AC-083):** дія-список `purchase.order.line` з доменом `[('td_date_ready', '>', <потрібна дата>), ('qty_received', '<', 'product_qty')]` і колонкою «Замовлення клієнтів» (compute з `reference_ids.sale_ids`).

## 2. Етап дошки (F-07) — зріз
`sale.order.td_stage` — selection compute, store (для групування канбана): «Пропозиція», «Очікує запуску», «У виробництві», «Виготовлено»; `td_mebli_install` додає `selection_add`: «Очікує клієнта», «Відвантажено / на доставці», «Монтаж», «Закрито». Inverse лише виконує стандартний старт МО з правами користувача для `mrp.group_mrp_user`; інакше UserError «Етап рахується з документів; запуск виробництва — лише начальник виробництва» (AC-064). Фільтр «Застряглі»: compute-пошук `td_is_stuck` за датою останньої зміни етапу (`td_stage_date`, datetime, store — **нове**) і `company.td_stuck_days` (AC-067).

## 3. Графік оплат (F-22) — зріз
`account.payment.term.line.td_milestone` — selection: `prepay` «Передоплата», `before_install` «Перед монтажем», `after_act` «Після акта» (ввід у довіднику умов оплати, «Облік → Налаштування → Умови оплати»). Суми етапів на замовленні — у `td_mebli_install` (контроль доплати).

## 4. Ціна з розмірів і собівартість до запуску (F-21, F-24) — зріз

| Назва поля (`sale.order.line`) | Тип | Звідки | Примітка |
|---|---|---|---|
| Параметричний (`td_is_parametric`) | related | товар | — |
| Ширина/Висота/Глибина, мм (`td_width`, `td_height`, `td_depth`) | integer compute, store | власні значення атрибутів (`product_attribute_custom_value.py:17`) | перевірка меж — §4 `td_mebli_mrp.md` |
| Коефіцієнт розмірів (`td_size_factor`) | float compute, store | формула категорії виробу | ціна рядка = ціна варіанта × коефіцієнт (`_compute_price_unit` успадковано) |
| Специфікація замовлення (`td_bom_id`) | m2o `mrp.bom` | генератор при підтвердженні | — |
| Планові матеріали / операції (`td_planned_material_cost`, `td_planned_operation_cost`) | monetary compute | деталі × `standard_price` × (1+відхід) / час × `costs_hour` | `groups` маржі (`security.md` §4) |

## 5. Зміна замовлення (F-44, S-18) — зріз

**`td.mebli.order.change`**

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Замовлення (`order_id`) | many2one `sale.order` | контекст | required, cascade |
| Компанія (`company_id`) | related `order_id.company_id`, store | — | **нове** (R-03) |
| Версія (`version`) | integer, readonly | max + 1 | required |
| Причина (`reason`) | selection: клієнт / компанія / постачальник | менеджер | required |
| Що змінюється (`note`) | char | менеджер | required |
| Стан (`state`) | selection: `open` «Змінюється» / `done` «Зафіксовано» / **`signed` «Підписано клієнтом»** (B) | кнопки | `signed` — нове |
| Ціна до / після, Обіцяна до / після | monetary / date, readonly | знімки `amount_total`, `commitment_date` | ставить система |
| Зсув, днів; Різниця ціни | integer / monetary compute, store | — | — |
| **Підпис клієнта (`signature`), Підписав (`signed_by`), Дата підпису (`signed_on`)** | image / char / datetime | портал (B) | **нове**; група `group_feature_change_sign` (AC-120) |

**Бізнес-правила.** (1) Одна відкрита зміна на замовлення (`td_change_open`); «Створити зміну» недоступна при відкритій. (2) Якщо будь-яку специфікацію рядка відправлено в розкрій — майстер пропонує лише «Дозамовлення» (новий рядок/МО), зміна відправлених деталей блокується (AC-119, AC-052). (3) «Зафіксувати» знімає «після», ставить `done`. (4) B: «Надіслати зміну на підпис» — портальне посилання на замовлення з блоком версії; підпис пише `signature`, `signed_on`, стан `signed`.

## 6. Договір і візуалізація (F-49, F-53) — зріз + доробки
- `sale.order.td_design_image` — image (1600×1600), ввід менеджера; блок «Візуалізація проєкту» в шаблоні пропозиції (`t-if`) (AC-032).
- Звіт «Договір» (`ir.actions.report`, `report_type='qweb-pdf'`) — `print-forms.md`. Режим — `company_id.td_contract_mode`; без значення — UserError AC-034 (AI-A08-05; у зрізі — `ir.config_parameter` з дефолтом «Підряд», R-04, R-05).

## 7. Подання й кнопки
- Форма замовлення: банер «Дата під загрозою: +N днів» (`invisible="td_delay_days <= 0"`), блок дат, вкладки «Закупівлі під замовлення», «Собівартість» (група маржі), «Зміни»; кнопки шапки «Створити зміну» (`invisible="state != 'sale' or td_change_open"`), «Друкувати договір», «Надіслати лист» (`td_mebli_notify`); смарт-кнопки «Виробництво», «Заміри», «Рекламації», «Не запаковано».
- Дошка S-05: `<kanban default_group_by="td_stage">` з червоною карткою при `td_delay_days > 0`, причина й дні; `<list>` з групуванням за `td_delay_reason`.

## 8. Синхронізація
Напрям — від стандартних документів до замовлення (МО, закупівлі, відвантаження, задачі, акти, рахунки → compute на `sale.order`), зворотного запису немає (виняток — inverse етапу §2). `td_forecast_date`, `td_stage` збережені — залежності `@api.depends` на збережені поля джерел (`mrp_production_ids.date_finished`, `td_task_ids.state`, `td_act_ids.state`, …); незбережені джерела (закупівлі через `reference_ids`) — перерахунок тригером запису `purchase.order.line` (`td_mebli_notify` викликає перерахунок і активність, AC-029).
