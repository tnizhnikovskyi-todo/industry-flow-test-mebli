# AC-COVERAGE — група G1 (продаж, замір, повідомлення, ФОП)

Модулі: `td_mebli_sale`, `td_mebli_measure`, `td_mebli_notify`, новий `td_mebli_multico` — версія `19.0.1.1.0`.
`migrations/19.0.1.1.0/post-migrate.py` — лише `td_mebli_measure` (префікс noupdate-послідовності `ЗМ-` → `ЗМ/%(year)s/`). Решта змін — нові поля або нові stored-поля з compute (заповнюються оновленням модуля), xmlid не перейменовано.
Прогін: база `test-mebli-a11g1`, `-i td_mebli_notify,td_mebli_measure,td_mebli_multico --test-tags /td_mebli_sale,/td_mebli_measure,/td_mebli_notify,/td_mebli_multico` → **71 тест, 0 failed, 0 error**. Контроль сусідів (той самий прогін + `/td_mebli_cutting,/td_mebli_dashboard,/td_mebli_install,/td_mebli_cost,/td_mebli_claim,/td_mebli_shop,/td_mebli_mrp,/td_mebli_purchase`, код G2 до коміту 0dab06b) — 220 тестів, падав лише мій AC-005 (виправлено в наступному прогоні).
Тексти помилок — дослівно за SPEC через `i18n/uk.po` (англійське джерело в коді); тести звіряють український текст повністю.

## Стан AC

| AC | модуль | стан | тест | що зроблено / примітка |
|---|---|---|---|---|
| AC-003 | td_mebli_measure | done | td_mebli_measure/tests/test_g1_measure.py::test_ac_003_no_free_windows | `td.mebli.measure.booking.no_slot_text`: порожній список вікон → банер «Немає вільних вікон за обраний період — збільште кількість днів або оберіть іншого замірника», список і кнопки вибору сховано, зустріч не створюється. Майстер не падає UserError (ТР §2), щоб менеджер міг змінити дні/замірника (G1-3) |
| AC-005 | td_mebli_measure | done | test_g1_measure.py::test_ac_005_number_company_and_smart_buttons | послідовність `ЗМ/%(year)s/` + 4 цифри (нові бази — дані, наявні — міграція); компанія із замовлення; смарт-кнопка «Заміри» на замовленні (була) і **на нагоді** (нова) |
| AC-006 | td_mebli_measure | done | test_g1_measure.py::test_ac_006_measurer_sees_own_sheets_without_prices; test_wave2.py::test_booking_rechecks_the_window_and_measurer_by_group | група `td_mebli_measure.group_td_mebli_measurer` («Замірник», привілей «Меблі») тепер implied лише `base.group_user` (без «Продажі: власні документи»); правило «свої заміри»; доступ RWCD до замір-листа/ніш/техніки; адреса й телефон покупця — compute з `sudo` (`td_address`, `td_phone`); `sale.order` — AccessError; меню Продажів сховано, своє меню «Заміри → Мої заміри / Мій календар»; замовлення й нагоду на формі він не змінює (`td_can_link`) |
| AC-007 | td_mebli_measure | done (код) / MANUAL (пристрій) | test_g1_measure.py::test_ac_007_cards_on_a_phone | ніші й техніка мають `<list>` + `<kanban>` + `<form>`: стандартний x2many на малому екрані бере kanban (`web/.../field.js`, `isSmall`); фото — `many2many_binary`. 390 px без прокрутки й камера — тур A-16 / пілот |
| AC-008 | td_mebli_measure | done | test_g1_measure.py::test_ac_008_does_not_fit_text_and_order_counter; test_measure.py::test_fridge_deeper_than_the_niche | текст «Не вміщається: глибше на 30 мм» (uk); `sale.order.td_measure_issue_count` + банер на замовленні; банер МО — був |
| AC-009 | td_mebli_measure | done | test_wave2.py::test_rules_find_what_does_not_fit | без змін |
| AC-010 | td_mebli_measure | done | test_g1_measure.py::test_ac_010_empty_sizes_are_not_checked | `td_check` = `unchecked`, `issue` «Не перевірено (немає розмірів)», `fits=True` → не в лічильнику; будь-який порожній розмір техніки або ніші (ТР §1) |
| AC-014 | td_mebli_sale | done | td_mebli_sale/tests/test_g1_sale.py::test_ac_014_three_products_three_boms_three_mos | тест: 3 рядки-вироби → 3 специфікації, 3 МО, смарт-кнопка «Виробництво» = 3 |
| AC-016 | td_mebli_sale | done | test_g1_sale.py::test_ac_016_ordinary_product_pricelist_price | тест: звичайний товар — ціна прайсу, коефіцієнт 1 |
| AC-018 | td_mebli_sale (+ base G0) | done | test_g1_sale.py::test_ac_018_margin_hidden_from_salesperson; td_mebli_base/tests/test_company_params.py::test_ac_018_* | `groups="td_mebli_base.group_margin_view,td_mebli_base.group_finance,sales_team.group_sale_manager"` на `sale.order.line.td_planned_material_cost/_operation_cost` і **на стандартних** `margin`, `margin_percent` (замовлення й рядок), `purchase_price`, `sale.report.margin` (перевизначення атрибута, як робить сам `sale_margin` з `base.group_user`); меню «Собівартість замовлень» — ті самі групи. Форма/список/звіт продавця без маржі; параметр увімкнено — бачить (G1-1) |
| AC-030 | td_mebli_notify | done | td_mebli_notify/tests/test_g1_notify.py::test_ac_030_letters_by_template; test_notify.py::test_new_date_letter_opens_the_composer | нові шаблони «Запис на замір» (`calendar.event`: дата, час, адреса `location`) і «Дата монтажу» (`project.task`: дата, адреса, сума); були «Нагадування про доплату», «Нова дата»; стандартний редактор листа з шаблоном → лист у чаті запису |
| AC-031 | td_mebli_notify | done | test_g1_notify.py::test_ac_031_reminder_days_by_the_company, test_ac_031_no_email; test_notify.py::test_install_reminder_tomorrow | константу `PAYMENT_DAYS = 3` замінено на `res.company.td_pay_reminder_days` (VP-07, компанія замовлення); один раз на дату виїзду; без email — нотатка «Нагадування не надіслано: немає email» + активність менеджеру (теж один раз) |
| AC-033 | td_mebli_sale | done | test_g1_sale.py::test_ac_033_lawyer_mark_goes_away; test_contract.py::test_contract_two_modes_and_schedule | позначка «Шаблон до перевірки юристом (№17)» — `t-if="not company.td_legal_checked"`; корінь звіту з класом `td_mebli_report` (AC-N.06) |
| AC-034 | td_mebli_sale | done | test_contract.py::test_ac_034_no_mode_error | G0; застарілі терміни `td_mebli_contract_mode` прибрано з `uk.po`/`.pot` (перегенеровано) |
| AC-035 | td_mebli_multico | done | td_mebli_multico/tests/test_multico.py::test_ac_035_* (4) | новий модуль (`depends: td_mebli_install`): `sale.order.td_install_company_id` (домен — дозволені компанії ≠ продавця, лише `base.group_multi_company`), `td_parent_order_id` (без check_company), `td_install_order_ids`; `action_confirm` створює замовлення-послугу в компанії ФОП правами користувача, рядок «Монтаж» **переноситься** (не дублюється), ціна — з рядка або 0 (VP-16 продавця), замовлення ФОП підтверджується → задача в проєкті ФОП (`project_id` company_dependent); немає доступу — «У вас немає доступу до компанії <ФОП> — монтаж від неї оформлює користувач цієї компанії»; скасування основного — активність менеджеру ФОП; смарт-кнопки в обох |
| AC-036 | td_mebli_measure, td_mebli_sale, td_mebli_multico | done (свої моделі) | test_g1_measure.py::test_ac_036_measurements_by_company; test_g1_sale.py::test_ac_036_changes_by_company; test_multico.py::test_ac_036_fop_order_hidden_from_the_tov_user | `td.mebli.order.change.company_id` (related, store) + глобальне правило `[('company_id','in',company_ids)]`; замір — правило було, додано тест; multico нових моделей не має (правило `sale.order` — стандарт) |
| AC-043 | td_mebli_sale | done | test_g1_sale.py::test_ac_043_installation_in_the_price | `sale.order.line._get_display_price` → 0 для послуги з `service_tracking` (задача), якщо `company.td_install_in_price` (VP-16); задача — стандарт `sale_project`. Без залежності від `sale_project` (поле читається за назвою, G1-4) |
| AC-064 | td_mebli_sale | done | test_g1_sale.py::test_ac_064_salesperson_cannot_drag_the_stage; test_order_dates.py::test_stage_drag_needs_manufacturing_rights | текст SPEC «Етап рахується з документів; запуск виробництва — лише начальник виробництва» |
| AC-066 | td_mebli_sale | done | test_g1_sale.py::test_ac_066_reason_on_the_card_and_grouping | `td_delay_reason` += `customer` «Клієнт», `distributor` «Порізка в дистриб'ютора»; поля прогнозу (`td_shop_date`, `td_forecast_date`, `td_delay_days`, `td_late_item`, `td_delay_reason`) **stored** (групування); перерахунок — `@api.depends` збережених джерел + запис `purchase.order(.line)` + `_td_recompute_forecast()` + щоденний cron; червона картка дошки з днями й причиною; список дошки з групуванням «Причина зсуву» (KPI 2); хук `_td_distributor_date()` — G2 його перевизначає (G1-2) |
| AC-067 | td_mebli_sale | done | test_g1_sale.py::test_ac_067_stuck_orders_follow_the_parameter; test_g1_notify.py::test_ac_124_briefing_sections | `td_stage_date` (datetime, stored; рухається в `_write_multi`, коли збережений етап реально змінився — після всіх override `_compute_td_stage`, зокрема install); `td_is_stuck` з `search` за `company.td_stuck_days` кожної обраної компанії — без перезапуску; фільтр «Застряглі» на дошці. Картка дашборда (`STUCK_DAYS`) — G3 |
| AC-083 | td_mebli_sale | done | test_g1_sale.py::test_ac_083_delayed_deliveries | `purchase.order.line.td_need_date` (дата руху компонента МО, інакше обіцяна дата), `td_late_days`, `td_is_late` (search), `td_sale_order_ids`, кнопка «Відкрити замовлення клієнта»; дія «Затримані поставки» — меню Склад → Операції (`stock.group_stock_user`) і Закупівлі → Замовлення |
| AC-119 | td_mebli_sale | done | test_g1_sale.py::test_ac_119_after_cutting_only_an_additional_order | `sale.order._td_cut_version()` = max `mrp.bom.td_cut_version` (G2, 0dab06b); майстер зміни: `kind` «Зміна» / «Дозамовлення», при відправленому — лише дозамовлення, «Зміна» → «Специфікацію відправлено в розкрій (версія N) — зміна лише дозамовленням»; тест на справжньому `_td_mark_sent_to_cutting()` і блоці деталей AC-052 |
| AC-120 | td_mebli_sale | done | test_g1_sale.py::TestG1ChangeSign::test_ac_120_change_signed_in_the_portal (HttpCase) | `td.mebli.order.change`: стан `signed` «Підписано клієнтом», `signature`, `signed_by`, `signed_on`, `td_sign_requested`; кнопка «Надіслати зміну на підпис» (FG `group_feature_change_sign`, без групи — AccessError) → редактор листа з шаблоном і посиланням на портал; блок «Зміни замовлення» в стандартному порталі замовлення з модалкою `portal.signature_form`; маршрут `/my/orders/<id>/change/<id>/sign` (токен доступу замовлення, як `portal_quote_accept`); повторний підпис / чужий токен — помилка |
| AC-124 | td_mebli_notify | done | test_notify.py::test_briefing*; test_g1_notify.py::test_ac_124_briefing_sections | додано розділи «Прострочені рекламації» (`repair.order.td_overdue` модуля claim, VP-13 — G3) і «Застряглі замовлення» (`td_is_stuck`, VP-10); cron 07:30 — був |
| AC-125 | td_mebli_notify | done | test_g1_notify.py::test_ac_125_nothing_to_report | `data['nothing']` → лише «Відхилень немає»; кожен розділ показується тільки з даними (без порожніх розділів) |

## NFR і feature-групи (свої модулі)

| AC | стан | примітка |
|---|---|---|
| AC-N.01 | done (свої 4) | `i18n/uk.po` + `.pot` перегенеровано експортом з бази (`odoo-bin i18n export`), усі терміни перекладено (порожніх msgstr немає); тіла шаблонів листів і брифінгу — повний переклад |
| AC-N.04 | done | версії `19.0.1.1.0`; міграція лише послідовності заміру |
| AC-N.06 | done (договір) | клас `td_mebli_report` у звіті «Договір» |
| AC-N.07 | done (свої) | `group_feature_change_sign` — кнопка й поле підпису зміни. Інших функцій коробки B у модулях G1 немає; multico — окремий модуль B (ставиться лише за VP-03 `multi_install_fop`) |

## Нові td_-поля / моделі (модель даних)

| Поле / модель | Аналог у стандарті / причина |
|---|---|
| `td.mebli.measure.td_address`, `td_phone`, `td_can_link`; `.appliance.td_check`; `sale.order.td_measure_issue_count`; `crm.lead.td_measure_count` | немає: compute (sudo лише адреси й телефону для замірника без прав продажу) |
| `td.mebli.measure.booking.no_slot_text` | немає (TransientModel) |
| `sale.order.td_stage_date`, `td_is_stuck` | стандарт не зберігає дату зміни етапу (етап — td_) |
| `sale.order` поля прогнозу → stored | були compute; store потрібен для групування (AC-066) |
| `purchase.order.line.td_need_date`, `td_late_days`, `td_is_late`, `td_sale_order_ids` | стандарт має `date_planned` і `on_time_rate`, але не «потрібно до» і не зачеплені замовлення |
| `td.mebli.order.change.company_id`, `kind`, `td_sign_requested`, `signature`, `signed_by`, `signed_on`, стан `signed` | підпис — за зразком `sale.order.signature/signed_by/signed_on` (портал `sale`), але для версії зміни, не для замовлення |
| `sale.order.td_install_company_id`, `td_parent_order_id`, `td_parent_order_name`, `td_install_order_ids`, `td_install_order_count` (multico) | міжкомпанійних правил у CE немає (ТР multico) |

## Рішення AI з ризиком

| # | Рішення | Ризик |
|---|---|---|
| G1-1 | AC-018: `groups` маржі поставлено на рівні **моделі** й на стандартних `margin`/`margin_percent`/`purchase_price`/`sale.report.margin` (не лише в поданнях пакета, як у `security.md` §4) | код інших модулів, що читає маржу через `read()`/`search_read` від імені користувача без цих груп, отримає AccessError (python-доступ до атрибута працює). Керівник з групою `td_mebli_dashboard.group_td_mebli_director` без фінансиста не бачить маржу у списках — G3/G0 мають включити `group_finance` у групу керівника (`security.md` §1) |
| G1-2 | AC-066: поля прогнозу зроблено stored; закупівлі й приймання не є stored-залежностями → перерахунок хуками запису й cron (щодня; notify — щогодини) | між подіями (напр. приймання на склад без запису рядка) дата/причина на дошці може відставати до прогону cron. «Клієнт» = остання зафіксована зміна з причиною «Клієнт», навіть якщо пізніше запізнився цех |
| G1-3 | AC-003: банер у майстрі замість UserError із ТР §2 | текст дослівний, але це не «помилка» — тур A-16 має перевіряти банер |
| G1-4 | AC-043: «Монтаж» = послуга з `service_tracking` ≠ `no` (будь-яка послуга, що створює задачу) | інша послуга із задачею (напр. дизайн-проєкт) теж стане 0 у режимі «монтаж у вартості» — уточнити в A-12 (окремий товар/категорія) |
| G1-5 | AC-035: без рядка послуги монтажу підтвердження з «Монтаж виконує» — помилка «Додайте в замовлення рядок послуги монтажу…» (SPEC такого тексту не має) | менеджер мусить додати рядок; рядок переноситься в ФОП і знімається з суми продавця |
| G1-6 | AC-006: група замірника лишилась у `td_mebli_measure` (xmlid не перенесено в `td_mebli_base.group_measurer`) | ALLOCATION/ТР називають base; перенесення — окремий крок з міграцією xmlid |
| G1-7 | AC-067: «застряглі» рахуються лише для підтверджених замовлень з етапом не «Пропозиція/Надіслано/Закрито» | якщо власник вважає застряглими й пропозиції — розширити домен |

## Хвости (для сесії після злиття)

1. G2 (`td_mebli_cutting`): прогноз зберігається — при зміні `return_date`/стану завдання розкрою треба викликати `orders._td_recompute_forecast()` (залежності `@api.depends` на завдання в `td_mebli_sale` немає); інакше дата оновиться лише cron.
2. G3: картка «Застряглі» дашборда — перейти на `sale.order.td_is_stuck` (одне джерело з фільтром дошки, VP-10); група керівника — включити `group_finance` (див. G1-1).
3. Демо (`td_mebli_demo`): `_cron_td_customer_reminders()` тепер повертає ще ключ `no_email`; номери замірів — `ЗМ/РРРР/NNNN`.
4. Оновлення наявної бази зрізу (`-u`) не проганялось: міграцію послідовності перевірено лише читанням; нові stored-поля обчислюються стандартно при оновленні.
