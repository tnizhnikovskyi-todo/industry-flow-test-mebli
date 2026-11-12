# `td_mebli_install` — виїзди, акти, етапи після «Виготовлено», контроль доплати, нарахування

**Призначення.** S-12 (F-15, F-38, F-39, F-40, F-56, F-58, друк F-49), S-05 етапи після «Виготовлено» (F-07, A4), контроль доплати (F-22, A1), S-17 нарахування (F-41, F-42). Коробка A. AC: AC-020, AC-021, AC-031 (дані), AC-063, AC-065, AC-095…AC-108.
**Звірка:** `addons/sale_project/models/product_template.py:22` (`service_tracking`); `addons/sale_project/models/project_task.py:25` (`sale_order_id`); `addons/project/models/project_task.py:168` (`state`), `:183` (`date_deadline`), `:205` (`user_ids`); `addons/project/security/project_security.xml:80` (`task_visibility_rule`); `addons/project/views/project_task_views.xml:829` (календар задач); `addons/web/static/src/views/fields/signature/signature_field.js:14`; `addons/account/models/account_move.py:565` (`amount_residual`), `:606` (`payment_state`); `addons/stock/models/stock_picking.py:594` (`scheduled_date`); `addons/mrp/models/mrp_workcenter.py:542` (`duration`). PLAN.md: `td.mebli.install.act/.defect`, `td.mebli.accrual`, `sale.order.td_pay_*`, `project.task.td_*`, `sale.order.td_stage` (`selection_add`).

## 1. Акт (`td.mebli.install.act`, `mail.thread`) — зріз + доробки

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Номер (`name`) | char, readonly | `ir.sequence` (`АКТ/%(year)s/`) | — |
| Виїзд (`task_id`) | m2o `project.task` | контекст | required, cascade |
| Компанія (`company_id`) | related `task_id.company_id`, store | — | **нове** (R-03) |
| Замовлення (`order_id`) | related `task_id.sale_order_id`, store | — | — |
| Бригада (`crew_user_ids`) | related `task_id.user_ids` | — | — |
| Вид (`kind`) | selection: «Акт етапу» / «Фінальний акт» | бригадир | required |
| Стан (`state`) | selection: чернетка / підписано | «Підписати» | — |
| Підпис клієнта (`signature`), Підписав (`signed_by`), Дата (`signed_on`) | image / char / datetime | віджет підпису | AC-097, AC-098 |
| Чек-лист (`checklist`) | text | default `company.td_act_checklist` | AI-A08-16 (R-16) |
| Недоліки (`defect_ids`), Відкриті (`defect_open_count`) | o2m / integer compute | — | — |
| Фото (`photo_ids`) | many2many `ir.attachment` | — | — |
| У фотоархів (`photo_archive`) | boolean | бригадир | constraint: лише з `photo_consent` (AC-100) |
| **Згода на публікацію фото (`photo_consent`)** | boolean | бригадир зі слів покупця / договір | **нове**; юридична форма — ВП-2 |
| % бригаді (`crew_pct`) | float | default `company.td_crew_pct` | у зрізі default 5.0 (R-04) |
| Сума бригади (`crew_amount`) | monetary compute, store | сума замовлення × % (фінальний акт) | — |
| Сума бригади при підписі (`crew_amount_signed`) | monetary, readonly | пишеться в «Підписати» | основа нарахування |
| Доплату отримано / Бракує / Режим (`pay_ok`, `pay_missing`, `pay_control`) | related `order_id.td_pay_*` | — | — |

**`td.mebli.install.defect`:** `act_id` (required, cascade), `name` (required), `photo` (image), `resolved` (boolean), **`company_id`** (related, store — нове). Недолік редагується, поки акт — чернетка.

**Кнопка «Підписати»** (`invisible="state != 'draft'"`): без `signature` — UserError «Немає підпису клієнта»; контроль доплати (§3); `signed_on = now`, `crew_amount_signed = crew_amount`, стан «підписано»; після підпису `write` на будь-яке поле, крім `photo_archive`, — UserError «Підписаний акт змінювати не можна» (AC-098).

## 2. Етапи дошки після «Виготовлено» (F-07) — зріз
`sale.order.td_stage` `selection_add`: «Очікує клієнта» (відвантаження перенесено за обіцяну дату — `scheduled_date` > `commitment_date`), «Відвантажено / на доставці» (відвантаження підтверджено, виїздів немає або не почато), «Монтаж» (є виїзд у роботі або підписаний фінальний акт без повної оплати — з позначкою «Немає доплати <сума>», AC-065), «Закрито» (фінальний акт підписано й `td_pay_missing == 0`). Залежності: `sale.order.td_task_ids` (o2m на збережене `sale_order_id`), `td_act_ids` (o2m).

## 3. Контроль доплати (F-22, AI-15) — зріз + доробки

| Назва поля (`sale.order`) | Тип | Звідки | Примітка |
|---|---|---|---|
| Перед монтажем потрібно (`td_pay_before_install`) | monetary compute | `amount_total` × частки рядків умов оплати з етапом `prepay` + `before_install` | — |
| Отримано (`td_pay_received`) | monetary compute | рахунки замовлення: сума − `amount_residual` (проведені, мінус повернення) + **ручні позначки** | стандартне `amount_paid` рахує лише онлайн-транзакції — не підходить |
| Бракує (`td_pay_missing`), Сплачено перед монтажем (`td_pay_ok`) | monetary / boolean compute | — | — |
| Режим (`td_pay_control`) | selection compute | `company_id.td_payment_control` | у зрізі — `ir.config_parameter` (R-04) |

**Нова модель `td.mebli.pay.mark`** (ручна позначка оплати, AI-A08-07, AC-021):

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Замовлення (`order_id`) | m2o `sale.order` | контекст | required |
| Компанія (`company_id`) | related, store | — | правило multi-company |
| Сума (`amount`) | monetary | фінансист | required, > 0 |
| Причина (`reason`) | char | фінансист | required; без неї — UserError «Вкажіть причину ручної позначки оплати» |
| Хто / коли | `create_uid`, `create_date` | система | лише читання; журнал у чаті замовлення |
| Скасовано (`cancelled`) | boolean | фінансист | позначка знімається, коли оплата прийшла обміном (AC-042) |

**Перевірка** (`_td_check_payment(action)`) на «Почати монтаж» (задача), створення акта й «Підписати акт»: `warn` — повідомлення-банер і запис у чаті, дія виконується; `block` — UserError «Монтаж заблоковано: не отримано доплату <сума>. Зверніться до менеджера» (AC-020). Поля на задачі й акті: `project.task.td_pay_ok`, `td_pay_missing`, `td_pay_control`, `td_order_currency_id` (related).

## 4. Денний план бригади (F-58) — хвиля 2
`project.task.td_address` (char compute: адреса доставки замовлення), `td_places` (char compute: місця з комплектувального листа); дія «Мій день» — `<kanban>`/`<list>` задач користувача на сьогодні; звіт QWeb «Денний план бригади» (`print-forms.md`). Розширення `res.users` — дія меню користувача (зріз хвилі 2).

## 5. Нарахування (`td.mebli.accrual`) — зріз + доробки

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Працівник (`employee_id`) | m2o `hr.employee` | розрахунок / майстер цеху | required, index |
| Дата (`date`) | date | — | required |
| Вид (`kind`) | selection: відрядна / % бригаді / премія / штраф | — | required |
| Години (`hours`) | float, readonly | рядки часу працівника | — |
| Розцінка (`piece_rate`) | monetary, readonly | `mrp.routing.workcenter.td_piece_rate` | — |
| Сума (`amount`) | monetary | розрахунок; премія/штраф — ввід | штраф — від'ємна |
| Причина (`reason_id`) | **many2one `td.mebli.accrual.reason`** | довідник | **нове**: required для премії/штрафу (AC-108); char `reason` зрізу лишається як «Коментар», міграція 19.0.1.1.0 створює причини з наявних текстів |
| Рядок часу (`productivity_id`), Дільниця (`workcenter_id`) | m2o / related, store | — | ключ ідемпотентності відрядної |
| Акт (`act_id`) | m2o `td.mebli.install.act` | — | ключ ідемпотентності % бригаді |
| Замовлення (`order_ref`) | char compute, store | — | — |
| Компанія (`company_id`) | m2o, required | — | правило є |
| Стан (`state`) | selection: чернетка / підтверджено | керівник | підтверджене — лише читання (правило) |
| **Передано в BAS (`bas_state`)** | selection: — / передано / помилка | `td_mebli_bas` | **нове** (AC-109) |

**Довідник `td.mebli.accrual.reason`** (новий): `name` (char, translate), `kind` (премія / штраф), `default_amount` (monetary), `company_id`, `active`. Меню «Нарахування → Налаштування → Причини премій і штрафів»; типовий набір 6–10 — дані конфіг-пакета.

**Майстер «Нарахувати» за період** (`td.mebli.accrual.wizard`, TransientModel — у зрізі дія на моделі): `date_from`, `date_to`, `company_id`; підсумок `missing_rate_count` і перелік операцій без розцінки (AC-105). Ідемпотентність: унікальність (`productivity_id`, `kind`) і (`act_id`, `employee_id`, `kind`) — `models.Constraint` UNIQUE. % бригаді: `crew_amount_signed` фінального акта (або етапів — `company.td_crew_base`), поділ — `company.td_crew_split` (AC-103, AC-104).

## 6. Права й UI
`security.md`: бригада бачить акти своїх виїздів і редагує чернетку; працівник — свої нарахування; майстер — нарахування своїх дільниць у чернетці; керівник підтверджує. Меню «Монтаж → Календар» (`<calendar date_start="date_deadline">` задач проєкту монтажів, фільтр за бригадою), «Монтаж → Акти», «Монтаж → Мій день», «Нарахування» (`<pivot>` за працівником і видом, `<list>`). Кнопки акта: «Підписати», «Додати недолік», «У фотоархів», «Друкувати акт».
