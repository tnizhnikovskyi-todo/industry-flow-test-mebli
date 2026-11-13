# `td_mebli_dashboard` і `td_mebli_notify` — дашборд керівника, табло цеху, сповіщення, листи, брифінг

**Призначення.** S-19 (F-45, F-64), табло цеху S-06 (F-65, B), сповіщення менеджеру (F-50), листи покупцю й нагадування (F-51). Коробка A (табло, 12-й показник — B). AC: AC-029…AC-031, AC-079, AC-121…AC-125.
**Звірка:** клієнтська дія `ir.actions.client` (`odoo/addons/base/models/ir_actions.py:1427`), реєстр дій веб-клієнта `registry.category("actions")` (`addons/web/static/src/webclient/actions/action_service.js:49`); у CE виробничого дашборда немає — каталоги `addons/spreadsheet_dashboard*` без `_mrp` (PLAN §2); `mail.activity` — `addons/mail/models/mail_activity.py:26`; `mail.template` — `addons/mail/models/mail_template.py:19`; `ir.cron` — `odoo/addons/base/models/ir_cron.py:112-113` (`interval_number`, `interval_type`); `calendar.alarm` — `addons/calendar/models/calendar_alarm.py:8`.

## 1. Дашборд (`td.mebli.dashboard`, AbstractModel-постачальник даних) — зріз

Клієнтська дія (OWL-компонент, корінь `.td_dash_grid`, картка `.td_card`) викликає `get_cards(company_ids)`; кожна картка повертає значення і домен для переходу — **той самий домен, яким рахувалась** (AC-121).

| № | Картка (BOX §11.1) | Джерело | Коробка |
|---|---|---|---|
| 1 | Замовлення в строк | змонтовані за період: дата фінального акта ≤ `commitment_date` | A |
| 2 | Зсув за причинами | `td_delay_days` згруповано за `td_delay_reason` | A |
| 3 | Застряглі | `td_is_stuck` (`company.td_stuck_days`) | A |
| 4 | Доплати після монтажу | `td_pay_missing` замовлень з підписаним актом | A |
| 5 | Рекламації на 100 замовлень, середній час закриття | `repair.order` з `td_claim_order_id` | A |
| 6 | Маржа план ↔ факт | `td_mebli_cost` (зважено) | A |
| 7 | Завантаження дільниць | `td_load_pct` на 7 днів | A |
| 8 | Конверсія замір → договір | зустрічі «Замір» нагод ÷ підтверджені замовлення з цих нагод | A |
| 9 | Готове, не відвантажене | `td_stage = 'waiting_customer'` + сума | A |
| 10 | Відходи розкрою | `td.mebli.cutting.job.waste_pct` з `result_source = 'imported'` | A (лише свій розкрій) |
| 11 | Ціни понад історію | `purchase.order.line.td_over_history` | A |
| 12 | Невідповідності якості | `td.mebli.quality.check.result = 'fail'` (+ брак кіоску) | B (`group_feature_quality`; на EE — з Quality через міст) |

Порожні дані — 0 або «Немає даних», без ділення на нуль (AC-123). Доступ — група `group_director`; дія й меню з `groups` (AC-122). Поле зрізу `sale.order.td_dash_paid`, `td_dash_due` (compute) — допоміжні для картки 4.

**Табло цеху (F-65, B)** — друга клієнтська дія `td_mebli_dashboard.shop_board` (зріз хвилі 2: `shop_board.py`), лише читання, автооновлення кожні 60 с (таймер OWL), доступ — `group_kiosk` + `group_feature_shop_board`: завдання зміни, зроблено за зміну, замовлення під загрозою, відставання дільниць (AC-079).

## 2. Сповіщення й листи (`td_mebli_notify`) — хвиля 2

| Елемент | Тип Odoo | Що робить | AC |
|---|---|---|---|
| Тип активності «Зсув прогнозної дати» | `mail.activity.type` (дані) | — | AC-029 |
| `sale.order._td_sync_forecast_activity()` | метод; викликається з `write` `purchase.order.line` (`date_planned`), `mrp.production` (`date_finished`) і cron | створює одну активність менеджеру (`user_id` замовлення) при `td_delay_days > 0`, оновлює текст (дата, причина), закриває (`action_done`) при поверненні в строк; ключ — тип активності + `res_id` (без дублів) | AC-029 |
| cron «Меблі: активності зсуву прогнозу» | `ir.cron`, 1 раз/день | страхувальний прохід відкритих замовлень | AC-029 |
| Шаблони листів | `mail.template` на `sale.order` / `project.task` / `calendar.event`: «Запис на замір», «Дата монтажу», «Нагадування про доплату», «Нова дата» | українською, `lang` = мова покупця | AC-030 |
| cron «Меблі: нагадування покупцям» | `ir.cron`, 1 раз/день, `project.task._cron_td_customer_reminders` | виїзди через `company.td_pay_reminder_days` з `td_pay_ok = False` → лист «Нагадування про доплату» один раз (позначка `td_reminder_sent_on` на задачі — **нове поле**, date); без email — нотатка в чаті й активність менеджеру | AC-031 |
| cron «Меблі: ранковий брифінг власника» | `ir.cron`, щодня 07:30 (`nextcall` за часовим поясом компанії) | збирає картки 1, 3, 4, 5 і простої дільниць; надсилає повідомлення в «Вхідні» користувачам `group_director` (і email, якщо є); без відхилень — «Відхилень немає» | AC-124, AC-125 |

Без AI (REJ-030 не порушено); Viber/SMS — поза обсягом (REJ-063).

## 3. UI/UX
Меню верхнього рівня «Меблі → Дашборд керівника» (група керівника) і «Меблі → Табло цеху» (кіоск, B). Картка: назва, значення, підпис-пояснення формули (tooltip), колір порогу; клік — `doAction` зі списком записів картки. Сітка — 1440×810 без прокрутки для 11 карток (рішення зрізу W3-1); на телефоні — одна колонка.
