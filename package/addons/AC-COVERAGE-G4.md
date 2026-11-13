# AC-COVERAGE-G4: інтеграції й мости EE (A-11, фаза збірки)

Виконавець G4 (бриф групи — `scratchpad/a11-rules.md`). Модулі групи: `td_mebli_ua`, `td_mebli_attendance`, нові `td_mebli_bas`,
`td_mebli_migration` і 6 мостів EE (`td_mebli_shopfloor`, `_quality`, `_fsm`, `_planning`, `_helpdesk`, `_sign`).
Версії модулів групи підняті до `19.0.1.1.0`. Прогін: `-i td_mebli_ua,td_mebli_attendance,td_mebli_bas,td_mebli_migration`
на чистій базі з префіксом `test-mebli-a11g4-*` (http-порт 8174) — **0 failed, 0 error** (30 тестів: ua 10, attendance 7,
bas 13, migration 12 — рахунок по модулях перекривається; окремі лічильники в «Тести»). Повна установка профілю A з
`td_mebli_bas,td_mebli_migration,td_mebli_demo` (без demo-даних) — усі модулі `installed`, 6 мостів `uninstalled` (AC-130).
`python -m py_compile` і перевірка XML через lxml — усі файли групи OK. Рядки інтерфейсу — у `i18n/uk.po` кожного модуля.

**Стани:** `done` — поведінку з Then реалізовано, є тест; `ee-bridge-code` — міст EE, код без запуску (на CE перевіряється
лише невстановлення й маніфест; тести EE під тегом `td_mebli_ee` спрацюють на Enterprise); `tail` — хвіст до іншої групи;
`MANUAL` — перевірити неможливо (EE або невідомий формат), причина в колонці.

## Таблиця AC

| AC | модуль | стан | тест | нотатка |
|---|---|---|---|---|
| AC-037 | `td_mebli_ua` | done | `test_ua.py::test_ac_037_cron_writes_the_nbu_source`, `::test_ac_037_update_prices_only_quotations`, `::test_ac_037_update_prices_needs_finance`, `::test_ac_037_menu_behind_the_feature_group` | курс НБУ у `res.currency.rate` (джерело «НБУ»); кнопка «Оновити ціни за курсом» (меню за `group_feature_nbu`, метод за `group_finance`) перераховує лише пропозиції `draft`/`sent` стандартним `_recompute_prices`, у чат — старий/новий підсумок; підтверджені не чіпає. **Зовнішніх викликів у тестах немає: НБУ — мок** (`_td_fetch_nbu`) |
| AC-038 | `td_mebli_ua` | done | `::test_ac_038_nbu_down_keeps_rates_and_warns_finance`, `::test_ac_038_fetch_rejects_a_broken_answer`, `::test_ac_038_uk_texts` | збій НБУ (мережа/формат/порожня відповідь) → курси не змінено, ERROR у лог, активність «Курс НБУ не оновлено» фінансистам (`group_finance`, одна на користувача); cron лишається щоденним. `nbu_online` вимкнено — онлайн за `ВП-5` (формат API наживо не перевіряв: без зовнішніх викликів) |
| AC-039 | `td_mebli_bas` | done | `test_bas.py::test_ac_039_daily_exchange_sends_sales_and_purchases`, `::test_ac_039_send_button_on_the_order`, `::test_ac_039_one_channel_per_company` | `td.mebli.bas.channel/.batch/.log`; cron «Меблі: обмін з BAS» і кнопки «Передати в BAS» (канал, замовлення) кладуть проведені `out_invoice/out_refund`, `in_invoice/in_refund` з кодом контрагента/товару в пакет (JSON чернеткової схеми `td_mebli_bas/0.1-draft`); статус «Передано», журнал. Формат BAS — **каркас до ВП-1**; транспорт `file` (BAS забирає файл), `http` — заглушка до контракту |
| AC-040 | `td_mebli_bas` | done | `::test_ac_040_partner_without_code_is_an_error_the_rest_goes`, `::test_ac_040_bas_rejects_a_document_or_the_batch` | документ без коду контрагента або відхилений BAS → «Помилка обміну» з причиною в журналі, решта пакета йде; «Повторити» (тільки `group_finance`) збирає помилкові в новий пакет |
| AC-041 | `td_mebli_bas` | done | `::test_ac_041_sent_invoice_is_locked_reversal_allowed`, `::test_ac_041_uk_text_is_the_spec_text` | `account.move` зі `td_bas_state='sent'`: `write` на суму/партнера/рядки, `button_draft`, `button_cancel` → UserError «Документ уже передано в BAS — виправлення лише сторно» (текст дослівно за SPEC/ТР, звірено з `uk.po`); сторно (`out_refund`) і чат дозволені |
| AC-042 | `td_mebli_bas` (+`td_mebli_install`) | done (+tail) | `::test_ac_042_payment_from_bas_reconciles_the_invoice`, `::test_ac_042_broken_file_is_a_batch_error` | вхідний пакет оплат → `account.payment`, звірка з рахунком за номером (`account.payment.register`), «Отримано»/контроль доплати замовлення оновлюються (`td_pay_received` з `td_mebli_install`); незіставлена — «Не зіставлено» в журналі + активність відповідальному; повторний імпорт не дублює (`td_bas_ref`). **ХВІСТ (G3):** скасування ручних позначок `td.mebli.pay.mark` (SPEC §1.3 п.3) — хук `_td_after_bas_payment` готовий, тіло дописати після появи моделі з G3 (AC-021); не дублюю |
| AC-078 | `td_mebli_attendance` (+`td_mebli_bas`) | done | `test_export.py::test_ac_078_file_columns_and_total`, `::test_ac_078_empty_period_gives_an_empty_file_with_a_warning`; `test_bas.py::test_ac_078_time_sheet_batch_with_the_bas_code` | CSV (працівник, табельний код, днів, годин) із підсумком; період без відвідувань — порожній файл з попередженням; код = `hr.employee.td_bas_code` (додає `td_mebli_bas`) або Badge ID; кнопка «Передати в BAS» кладе файл у пакет виду «табель». Прибрано слово «імітація» (замінено на «чернетковий формат контракту, ВП-1») |
| AC-089 | `td_mebli_migration` | done (каркас) | `test_migration.py::test_ac_089_bas_converter_keeps_the_bas_code`, `::test_ac_089_missing_columns_are_reported`, `::test_ac_089_report_reconciled_when_equal`, `::test_ac_089_import_steps_follow_the_templates_of_a13` | модель `td.mebli.migration.step` (порядок імпорту CSV-шаблонів A-13 — **посилається на `package/master-data`, CSV не дублює**, кнопка відкриває стандартний `base_import`); конвертори `scripts/convert_bas.py`, `convert_bazis.py` — **каркас (формати BAS/БАЗИС невідомі, ВП-1/ВП-3)**: мапінг-ядро export→CSV, чернеткова карта колонок, запуск поза Odoo (B-06). Звіт звірки `td.mebli.migration.check(.line)`: передоплати/кількість відкритих/залишок, Odoo проти джерела, PDF |
| AC-090 | `td_mebli_migration` | done | `::test_ac_090_difference_shows_the_causes_and_needs_a_signed_explanation` | стан «розбіжність» з різницею й записами-причинами (`cause_order_ids`); «звірено» лише при 0, «пояснено» — лише з поясненням, підписаним керівником (`group_sale_manager`); `ValidationError`/`AccessError` на обхід |
| AC-109 | `td_mebli_bas` | done | `::test_ac_109_confirmed_accruals_into_the_sheet` | `td.mebli.accrual.bas_state`/`bas_batch_id` через `_inherit`; «Передати в BAS» (кнопка в списку нарахувань, `group_finance`) — відомість за працівником і видом нарахування, лише підтверджені; передані змінити/видалити → UserError «лише сторно» |
| AC-113 | `td_mebli_helpdesk` | ee-bridge-code | `test_ee_bridge.py` (тег `td_mebli_ee`) | міст `depends: td_mebli_claim, helpdesk`, `auto_install`; тікет ↔ замовлення/деталь/рекламація (`repair.order`), «Повторне виготовлення» з тікета, канбан рекламацій ховається групою. **MANUAL на EE (ВП-4):** поля Helpdesk — припущення, перевіряє тест на EE |
| AC-126 | `td_mebli_shopfloor` | ee-bridge-code | `test_ee_bridge.py` (`td_mebli_ee`) | `depends: td_mebli_shop, mrp_workorder`; деталі (`td_part_ids`) і причини паузи (стандартні `productivity.loss`) у робочому завданні; кіоск td_ і меню планшета — ховає `post_init_hook` (знімає `group_feature_kiosk`). MANUAL на EE |
| AC-127 | `td_mebli_quality` | ee-bridge-code | `test_ee_bridge.py` (`td_mebli_ee`) | `depends: td_mebli_shop, quality_control`; точки якості з `td_quality_point` операцій → `quality.point` (не дублюються); дашборд читає `quality.check` з `quality_state='fail'`; `group_feature_quality` знімається хуком. MANUAL на EE |
| AC-128 | `td_mebli_fsm`, `td_mebli_planning` | ee-bridge-code | `test_ee_bridge.py` (`td_mebli_ee`) | fsm: `depends: td_mebli_install, industry_fsm`, акт і % бригаді на задачі FSM; planning: `depends: td_mebli_install, planning`, кнопка «Запланувати бригаду» → `planning.slot` на дату виїзду. MANUAL на EE |
| AC-129 | `td_mebli_sign` | ee-bridge-code | `test_ee_bridge.py` (`td_mebli_ee`) | `depends: td_mebli_install, sign`; міксин `td.mebli.sign.mixin` на `sale.order` і `td.mebli.install.act`: PDF нашого звіту → `sign.template` + майстер `sign.send.request`; підписаний файл (`state='signed'`) → чат запису. MANUAL на EE |
| AC-130 | 6 мостів | done (CE) | `td_mebli_migration/tests/test_ee_bridges_ce.py::test_ac_130_no_bridge_on_community` | у чистій CE жоден міст не встановлено, без помилок залежностей; маніфести: `auto_install=[ядро, EE-додаток]`, `depends` = ядро+EE, `license=LGPL-3`. Повна установка профілю A це підтвердила (6 мостів `uninstalled`). Установка на EE — **MANUAL (ВП-4)** |

### Нефункціональні (частка G4)
| AC | стан | нотатка |
|---|---|---|
| AC-N.01 | done (G4-частина) | `i18n/uk.po` у всіх 10 модулях групи, усі рядки перекладено (нові `td_mebli_bas`, `td_mebli_migration`, 6 мостів; оновлено `td_mebli_ua`, `td_mebli_attendance`). Мости — файл написано вручну (на CE не встановлюються, експорт неможливий) |
| AC-N.07 | done (G4-частина) | `group_feature_nbu` навішено на меню «Оновити ціни за курсом» (`td_mebli_ua`); feature-групи `kiosk`/`quality` знімають хуки мостів (функцію B замінює додаток EE) |

## Назви модулів EE (звірено з заглушками CE `ir_module_module.xml` і знанням Odoo 19)
`mrp_workorder` (Shop Floor), `quality_control` (Quality), `industry_fsm` (Field Service), `planning` (Planning),
`helpdesk` (Helpdesk), `sign` (Sign) — рядки заглушок у `odoo/addons/base/data/ir_module_module.xml` присутні.
Поля/методи цих моделей у мостах — **припущення до ВП-4**, перевіряє тест під тегом `td_mebli_ee` (запуститься на Enterprise).

## Нові td_-поля/моделі (таблиця моделі даних) — аналог/причина
| Поле / модель | Модуль | Аналог у стандарті / причина |
|---|---|---|
| `td.mebli.bas.channel/.batch/.log` | `td_mebli_bas` | немає стандартного обміну з BAS — наша черга (AC-039) |
| `res.partner/product.product/hr.employee.td_bas_code` (`company_dependent`) | `td_mebli_bas` | зовнішній код у базі BAS кожної юрособи; стандартний `ref` — внутрішній (AC-039) |
| `account.move.td_bas_state/td_bas_batch_id` | `td_mebli_bas` | стандарт не має статусу зовнішнього обміну (AC-039, AC-041) |
| `account.payment.td_bas_ref` | `td_mebli_bas` | ідемпотентність імпорту оплат (AC-042) |
| `sale.order.td_bas_state` (compute) | `td_mebli_bas` | **замінює імітацію зрізу в `td_mebli_ua` (R-06)**; значення з рахунків |
| `td.mebli.accrual.bas_state/bas_batch_id` | `td_mebli_bas` | статус передачі нарахувань (AC-109) |
| `td.mebli.migration.check(.line)`, `td.mebli.migration.step` | `td_mebli_migration` | звірка міграції й порядок імпорту (AC-089, AC-090) |
| `mrp.workorder.td_part_ids`, `mrp.routing.workcenter._td_sync_quality_points`, `planning.slot.td_task_id`, `helpdesk.ticket.td_*`, `td.mebli.sign.mixin` | мости EE | зв'язок td_-даних зі стандартним додатком EE (AC-113, AC-126…AC-129) |

## Рішення AI з ризиком
| # | Рішення | Ризик |
|---|---|---|
| G4-1 | Формат пакета BAS — власна чернеткова JSON-схема `td_mebli_bas/0.1-draft` (транспорт `file`); `http` — заглушка (TdBasRejected) до ВП-1 | коли франчайзі дасть контракт, схему й транспорт переробити; A-14 матиме WARN (ВП-1) |
| G4-2 | `td_bas_code` — `company_dependent=True` (у кожної юрособи своя база BAS) | значення не копіюється між компаніями; для коробки A (одна юрособа) різниці немає |
| G4-3 | `sale.order.td_bas_state` зроблено compute з рахунків замовлення (R-06): імітацію-поле зрізу в `td_mebli_ua` видалено | **`td_mebli_demo/full.py` ще пише `td_bas_state` напряму — це впаде при demo-даних з `td_mebli_bas`**; демо — крок сесії після G1–G4 (писати стан через проведення рахунку + «Передати в BAS»). Записав як ХВІСТ нижче |
| G4-4 | Конвертори BAS/БАЗИС — CLI-каркас поза Odoo з чернетковою картою колонок; реальна карта — файл `--mapping` на зразках клієнта (B-06) | до зразків формат невідомий (ВП-1, ВП-3); тест перевіряє лише ядро мапінгу й захист від CSV-ін'єкції |
| G4-5 | Поля/методи моделей EE в мостах — припущення за `tr/ee-bridges.md`; тести під тегом `td_mebli_ee` не йдуть на CE | на EE назви полів можуть відрізнятися — тест упаде й покаже, що правити (ВП-4) |
| G4-6 | НБУ онлайн (`nbu_online`) лишив вимкненим; формат API наживо не перевіряв (заборона зовнішніх викликів у тестах) | ВП-5: перевірити формат відповіді НБУ наживо до ввімкнення |
| G4-7 | `td_mebli_migration` залежить від `td_mebli_sale`, `sale_stock`, `base_import` (а не лише `td_mebli_sale`): звірка читає `qty_available` і `qty_delivered` | менша автономність модуля; усі залежності вже в профілі A |

## Хвости (доробити сесії після злиття груп)
1. **AC-042 (G3):** у `td_mebli_bas/models/bas_channel.py::_td_after_bas_payment` дописати скасування `td.mebli.pay.mark` того самого замовлення на ту саму суму (SPEC §1.3 п.3), коли модель з G3 (AC-021) існуватиме. Хук уже викликається після звірки оплати.
2. **Демо (G4-3):** `td_mebli_demo/full.py` (рядки ~539–540) пише `sale.order.td_bas_state` напряму — тепер це compute. З `td_mebli_bas` у базі demo-дані впадуть. Демо має ставити стан через «Передати в BAS» (проведений рахунок → пакет) або лишати `none`. Демо — крок сесії, не G4.
3. **`migrations/` версії `19.0.1.1.0`:** не додавав — у модулях групи немає перейменувань/видалень збереженої структури (`sale.order.td_bas_state` зрізу був не збережений compute-less Selection у `td_mebli_ua`; нове поле — compute без стовпця, старе прибрано разом з модулем-джерелом). Якщо A-14 вимагатиме явний drop стовпця — додати `migrations/19.0.1.1.0/pre-migrate.py` у `td_mebli_ua`.

## Відкриті питання
Нових відкритих питань до людини немає (ВП-1, ВП-3, ВП-4, ВП-5 уже в `SPEC §11.1` і `tests/open-questions.md`). Каркасні рішення за ними — у «Рішення AI з ризиком».
