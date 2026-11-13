# AC-COVERAGE: покриття AC кодом `td_mebli_*` (A-11, фаза 1: аналіз розриву)

Вхід: `package/ALLOCATION.md` (рядки з кроком A-11; «A-11 + значення VP A-12»; «A-12 (+ A-11: модуль)»), `package/SPEC.md` §4 (Given/When/Then), `package/tr/*`, ескалації `tests/reports/A-12.md` і `A-13.md`, код `package/addons/` (15 модулів зрізу A-21, гілка `flow/A-11-test`). Звірка API — `/home/user/odoo19/src` (Odoo 19.0 CE). Odoo-база не використовувалась: висновок зроблено з читання коду й назв тестів, тести не запускались.

**Стани:** `done` — поведінку з Then реалізовано, є тест (`модуль/tests/файл::метод`); `code-no-test` — код є, тесту на цей AC немає; `partial` — частина Then є, чого бракує — у колонці «що зробити»; `missing` — коду немає; `ee-bridge` — міст до EE (модуля немає, пишемо лише код: EE недоступна, SPEC ВП-4).
**Позначки в «що зробити»:** `[G0]`…`[G4]` — група плану збірки; `VP-xx →` — константа або `ir.config_parameter` зрізу замінюється полем `res.company.td_*` з `td_mebli_base`; `FG:` — потрібна feature-група коробки B (`td_mebli_base.group_feature_*`, `tr/00-architecture.md` §3). Жодної feature-групи в коді зрізу немає: функції B зараз видно в коробці A.
**Розбіжність модуля** (ALLOCATION ≠ факт) — позначено «⚠» і запропоновано рішення з меншим ризиком.

## Таблиця AC

| AC | модуль (ALLOCATION) | модуль (факт) | стан | тест | що зробити |
|---|---|---|---|---|---|
| AC-002 | td_mebli_measure | td_mebli_measure | done | td_mebli_measure/tests/test_wave2.py::test_free_windows_and_booking | — |
| AC-003 | td_mebli_measure | td_mebli_measure | partial | — | [G1] майстер `td.mebli.measure.booking` при порожньому `slot_ids` показує лише порожній список: додати compute-текст «Немає вільних вікон за обраний період…» у формі, кнопку вибору вікна не показувати; тест |
| AC-005 | td_mebli_measure | td_mebli_measure | partial | td_mebli_measure/tests/test_measure.py::test_own_measurements_and_lead_from_the_order | [G1] послідовність `td.mebli.measure` має префікс `ЗМ-`, SPEC — `ЗМ/РРРР/NNNN` (`prefix` `ЗМ/%(year)s/`, `padding` 4) — дані `ir_sequence_data.xml` з `noupdate`: змінити через міграцію; тест на номер |
| AC-006 | td_mebli_measure, td_mebli_base | td_mebli_measure | partial | td_mebli_measure/tests/test_wave2.py::test_booking_rechecks_the_window_and_measurer_by_group | [G1] група зрізу `group_td_mebli_measurer` включає `sales_team.group_sale_salesman` → замірник бачить ціни й маржу замовлень (суперечить Then). Група без прав продажу + related-поля адреси й телефону на замір-листі; тест AccessError на `sale.order`. ⚠ ALLOCATION називає `td_mebli_base` (група `group_measurer`, `tr/security.md` §1): менший ризик — виправити групу на місці в `td_mebli_measure`, перенесення в base — пізніше з міграцією xmlid |
| AC-007 | td_mebli_measure | td_mebli_measure | code-no-test | — | [G1] форма замір-листа з `many2many_binary` для фото є; ніші й техніка — список, не картки: додати `<kanban>`-подання для one2many на мобільному; тест рендеру форми (камера — пілот) |
| AC-008 | td_mebli_measure | td_mebli_measure | done | td_mebli_measure/tests/test_measure.py::test_fridge_deeper_than_the_niche | [G1] звірити текст «Не вміщається: глибше на 30 мм» з `i18n/uk.po` |
| AC-009 | td_mebli_measure | td_mebli_measure | done | td_mebli_measure/tests/test_wave2.py::test_rules_find_what_does_not_fit | — |
| AC-010 | td_mebli_measure | td_mebli_measure | partial | — | [G1] `_compute_fits`: при порожніх розмірах ніші чи техніки зараз пише «fits»; потрібен стан «Не перевірено (немає розмірів)», який не рахується в «Не вміщається»; тест |
| AC-011 | product, td_mebli_mrp (A-12 з модулем A-11) | td_mebli_mrp, td_mebli_sale | done | td_mebli_sale/tests/test_configurator_tour.py::test_configurator_dimensions | Виключення атрибутів — дані A-12. [G2] FG: `group_feature_configurator` на полях розмірів рядка |
| AC-012 | td_mebli_mrp | td_mebli_mrp, td_mebli_sale | done | td_mebli_mrp/tests/test_order_bom.py::test_out_of_range; td_mebli_sale/tests/test_sale_line.py::test_invalid_dims | [G2] FG: `group_feature_configurator`; звірити текст помилки з SPEC |
| AC-013 | td_mebli_mrp, td_mebli_sale | td_mebli_mrp, td_mebli_sale | done | td_mebli_mrp/tests/test_order_bom.py::test_generate; td_mebli_sale/tests/test_sale_flow.py::test_confirm_creates_mo | — |
| AC-014 | td_mebli_sale | td_mebli_sale | code-no-test | — | [G1] тест: одне замовлення з 3 рядками-виробами → 3 специфікації, 3 МО, смарт-кнопка «Виробництво» (є лише `test_sale_flow.py::test_two_orders_two_boms` — два замовлення) |
| AC-015 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_sale_line.py::test_price | ≤ 3 с — вимір A-15 |
| AC-016 | td_mebli_sale | td_mebli_sale | code-no-test | — | [G1] тест: непараметричний товар — ціна прайс-листа, `td_size_factor` не застосовано |
| AC-017 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_sale_flow.py::test_margin; td_mebli_mrp/tests/test_order_bom.py::test_bom_cost | Видимість — AC-018 |
| AC-018 | td_mebli_base | — | missing | — | [G0] `res.company.td_margin_to_salesman` (VP-08), група `group_margin_view`, синхронізація групи в `write` компанії; [G1] `groups=` на `td_planned_*_cost` і поля маржі у видах `td_mebli_sale` (`sale_margin` — стандарт без груп); тест |
| AC-019 | account, td_mebli_sale (A-12 з модулем A-11) | td_mebli_sale, td_mebli_install | done | td_mebli_sale/tests/test_contract.py::test_contract_two_modes_and_schedule; td_mebli_install/tests/test_payment.py::test_due_before_installation_from_the_terms | Розмітка `td_milestone` етапів — дані A-12 (ескалація A-12 п.5) |
| AC-020 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_payment.py::test_warn_by_default_block_by_parameter, test_settings_parameter | [G0][G3] VP-06 → `res.company.td_payment_control` замість `ir.config_parameter` `td_mebli_install.payment_control` (ескалація A-12 п.3); перенесення значення — `post_init_hook` base |
| AC-021 | td_mebli_install | — | missing | — | [G3] модель `td.mebli.pay.mark` (order_id, amount, reason required, user, date, company_id), кнопка «Оплату підтверджено вручну» (групи finance/director, `tr/security.md` §2); `_td_paid_amount` її враховує; запис у чат; тести: без причини → помилка, менеджер/бригадир → AccessError |
| AC-022 | td_mebli_sale | td_mebli_sale (+ td_mebli_cutting причина) | done | td_mebli_sale/tests/test_order_dates.py::test_late_supplier_date_moves_the_forecast, test_workshop_shift_is_the_company_reason | — |
| AC-023 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_order_dates.py::test_quotation_the_workshop_decides | — |
| AC-024 | stock, purchase_stock, td_mebli_sale (A-12 з модулем A-11) | td_mebli_sale | done | td_mebli_sale/tests/test_order_dates.py::test_confirmation_creates_the_purchase_by_the_standard, test_late_supplier_date_moves_the_forecast | Маршрути MTO + «Купити» — дані A-12/A-13 |
| AC-025 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_wave2.py::test_supplier_delay_moves_the_forecast, test_early_deliveries_count_as_on_time | — |
| AC-026 | td_mebli_cutting | td_mebli_cutting | done | td_mebli_cutting/tests/test_distributor.py::test_send_to_distributor_is_a_standard_purchase, test_cutting_moves_the_forecast_date | [G2] VP-09: механізм «меню власного розкрою ховається для `distributor`» відсутній (ALLOCATION VP-09) — поле `res.company.td_cutting_mode` [G0] або група; тест |
| AC-027 | td_mebli_cutting | td_mebli_cutting | done | td_mebli_cutting/tests/test_distributor.py::test_no_cutting_service_is_explained | — |
| AC-028 | td_mebli_cutting | td_mebli_cutting | partial | td_mebli_cutting/tests/test_cutting_done.py::test_flow_states_and_file | [G2] на завданні немає номера версії специфікації й дати відправлення: поля `td.mebli.cutting.job.bom_version`, `sent_date` (readonly), `export_attachment_id` незмінний після `sent`; тест |
| AC-029 | td_mebli_notify | td_mebli_notify | done | td_mebli_notify/tests/test_notify.py::test_activity_created_once_updated_and_closed, test_activity_done_is_not_reopened_for_the_same_shift | — |
| AC-030 | mail, td_mebli_notify (A-12 з модулем A-11) | td_mebli_notify | partial | td_mebli_notify/tests/test_notify.py::test_new_date_letter_opens_the_composer, test_letter_queued_for_the_customer | [G1] є шаблони «Нова дата», «Нагадування про доплату», «Монтаж завтра»; бракує «Запис на замір» (`mail.template` на `crm.lead`/`calendar.event`) і явного «Дата монтажу»; тест |
| AC-031 | td_mebli_notify | td_mebli_notify | partial | td_mebli_notify/tests/test_notify.py::test_install_reminder_tomorrow | [G1] VP-07 → `res.company.td_pay_reminder_days` (зараз константа `PAYMENT_DAYS = 3`, SPEC типово 2); покупець без email — запис у чаті «Нагадування не надіслано: немає email» + активність менеджеру; тест саме на доплату |
| AC-032 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_wave2.py::test_design_visual_in_the_quotation | — |
| AC-033 | td_mebli_sale | td_mebli_sale | partial | td_mebli_sale/tests/test_contract.py::test_contract_two_modes_and_schedule | [G0][G1] режим з `ir.config_parameter` `td_mebli_sale.contract_mode` = `work/sale` → `res.company.td_contract_mode` = `contract/sale` (схема `answers.yaml`, ескалація A-12 п.3); `td_legal_checked` прибирає позначку юриста; прибрати поле `td_mebli_contract_mode` з `res.config.settings` зрізу |
| AC-034 | td_mebli_sale, td_mebli_base | — | missing | — | [G1] без режиму (`unset` → порожньо) — UserError «Задайте режим договору в налаштуваннях компанії…», PDF не формується (зараз default `work`); тест |
| AC-035 | td_mebli_multico | — | missing | — | [G1] новий модуль `td_mebli_multico` (`tr/td_mebli_multico.md`): поля `sale.order.td_install_company_id`, `td_parent_order_id`, `td_install_order_ids`, створення замовлення-послуги в компанії ФОП при `action_confirm`; тест |
| AC-036 | td_mebli_base | td_mebli_measure, td_mebli_install (лише 2 моделі) | partial | td_mebli_install/tests/test_install.py::test_accrual_of_another_company_is_hidden | Глобальні `ir.rule` `[('company_id','in',company_ids)]` є лише на `td.mebli.measure` і `td.mebli.accrual`. Бракує: `td.mebli.cutting.job` (+sheet/placement/offcut через job) [G2], `td.mebli.kit.line`, `td.mebli.quality.check` [G2], `td.mebli.order.change` [G1], `td.mebli.install.act`/`.defect` [G3]; тест на кожен модуль. ⚠ ALLOCATION: `td_mebli_base`; правило мусить лежати в модулі, що визначає модель (base їх не знає) — виправити рядок ALLOCATION на «кожен модуль з td-моделлю» (ризик менший, ніж зворотні залежності) |
| AC-037 | td_mebli_ua | td_mebli_ua | partial | td_mebli_ua/tests/test_ua.py::test_rates_into_the_standard_rate_table | [G4] кнопка «Оновити ціни за курсом»: лише чернетки (`state in ('draft','sent')`), у чаті старий/новий підсумок; FG: `group_feature_nbu`; тест |
| AC-038 | td_mebli_ua | td_mebli_ua | partial | — | [G4] `_td_cron_nbu` лише пише в лог: додати активність фінансисту «Курс НБУ не оновлено» (`activity_schedule`, `addons/mail/models/mail_activity_mixin.py:373`); тест з підміною `_td_fetch_nbu` |
| AC-039 | td_mebli_bas | — | missing | — | [G4] новий `td_mebli_bas` (`tr/integrations.md` §1): `td.mebli.bas.channel`, `.batch`, `.log`, `td_bas_code` (company_dependent), `account.move.td_bas_state`, cron, «Передати в BAS»; тест пакета |
| AC-040 | td_mebli_bas | — | missing | — | [G4] стан «Помилка обміну» з причиною в журналі, решта пакета передається, «Повторити» (finance); тест |
| AC-041 | td_mebli_bas | — | missing | — | [G4] `account.move.write`/`button_draft` при `td_bas_state='sent'` → UserError «Документ уже передано в BAS — виправлення лише сторно»; тест |
| AC-042 | td_mebli_bas, td_mebli_install | — | missing | — | [G4] імпорт оплат BAS → `account.payment` зі звіркою за номером рахунку, «Не зіставлено» в журналі; оновлює «Отримано»/контроль доплати (залежить від AC-021 [G3]); тест |
| AC-043 | sale_project (A-12; поле VP-16 — A-11) | — | missing | — | [G0] `res.company.td_install_in_price`; [G1] рядок послуги «Монтаж» з нульовою ціною в режимі «у вартості»; тест (A-11 частина рядка A-12) |
| AC-045 | td_mebli_mrp | td_mebli_mrp | partial | td_mebli_mrp/tests/test_spec_import.py::test_columns_are_recognized_by_their_titles; td_mebli_mrp/tests/test_wave2.py::test_excel_file_is_imported_like_csv | [G2] режим «Замінити деталі» (типово) / «Додати» (зараз лише додає), у чаті — режим; тест заміни |
| AC-046 | td_mebli_mrp | td_mebli_mrp | code-no-test | — | [G2] текст за SPEC «У файлі не знайдено колонок: Ширина…» (зараз «Columns not recognized…» з переліком знайдених); тест |
| AC-047 | td_mebli_mrp | — | missing | — | [G2] невідомий матеріал зараз мовчки підміняється першою плитою специфікації: перегляд рядків «Матеріал не знайдено» з номерами, блок імпорту; тест |
| AC-048 | td_mebli_mrp | td_mebli_mrp | code-no-test | — | [G2] тест імпорту 300 деталей (функціональний; час ≤ 30 с — вимір A-15) |
| AC-049 | td_mebli_mrp | — | missing | — | [G2] модель `td.mebli.import.template` (назва, сигнатура заголовків, мапінг) — її чекає й A-13 (ескалація A-13); ручне зіставлення й застосування за сигнатурою; права за `tr/security.md` §2; тест |
| AC-050 | td_mebli_mrp | — | missing | — | [G2] FG: `group_feature_ai_mapping`; параметр постачальника моделі; назовні — лише заголовки й ≤ 10 рядків без даних покупця; без AI — ручний мапінг. Ризик DATA_POLICY: за замовчуванням вимкнено, зовнішній виклик у тестах підміняти |
| AC-051 | td_mebli_mrp, td_mebli_sale | td_mebli_mrp, td_mebli_sale | done | td_mebli_mrp/tests/test_parts_view.py::test_production_shows_the_parts_of_its_bom, test_workorder_shows_the_parts_of_its_production | — |
| AC-052 | td_mebli_mrp | — | missing | — | [G2] поле `mrp.bom.td_cut_version` (ставить `td_mebli_cutting` при відправленні) і заборона `write`/`unlink` `td.mebli.part` з повідомленням «Специфікацію відправлено в розкрій (версія N)…»; тест. Потрібне для AC-119 [G1] |
| AC-053 | td_mebli_cutting | td_mebli_cutting | done | td_mebli_cutting/tests/test_cutting_done.py::test_flow_states_and_file | Імпорт результату — AC-131 |
| AC-054 | td_mebli_cutting | td_mebli_cutting | partial | — | [G2] `action_td_create_cutting_job` мовчки відкидає МО без деталей: помилка «У виробничому замовленні <номер> немає деталей розкрою»; тест |
| AC-055 | td_mebli_cutting, td_mebli_measure | td_mebli_cutting | done | td_mebli_cutting/tests/test_measure_gate.py::test_warning_then_send_anyway, test_no_problem_no_question | — |
| AC-056 | td_mebli_cutting | td_mebli_cutting | partial | — | [G2] замовлення без замір-листа — попередження «Замір не заповнено — перевірку пропущено» (запис у чат завдання), не блокує; тест |
| AC-057 | td_mebli_cutting | td_mebli_cutting | partial | — | [G2] кілька МО в завданні вже можна; тест на 3 МО одного декору, МО/замовлення деталі видно в списку деталей завдання; FG: `group_feature_cutting_batch` |
| AC-058 | td_mebli_cutting | — | missing | — | [G2] перевірка «одне завдання — один матеріал плити» при створенні (зараз групує за матеріалом без помилки); тест |
| AC-059 | td_mebli_cutting | td_mebli_cutting | done | td_mebli_cutting/tests/test_cutting_done.py::test_reserve_and_offcuts, test_offcut_valuation | [G2] VP-12 → default `min_offcut_mm` з `res.company.td_min_offcut_mm` (зараз 300 у коді); FG: `group_feature_offcut` |
| AC-060 | td_mebli_cutting | td_mebli_cutting | partial | td_mebli_cutting/tests/test_simulator.py::test_offcut_reuse_first, test_job_uses_offcut_lot_first | [G2] автопідбір обрізків в імітаторі є; бракує кнопки «Підібрати обрізок» під деталь (той самий матеріал, ≥ розміру з поворотом, резерв під завдання); тест |
| AC-061 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_wave2.py::test_labels_with_qr, test_one_label_per_piece_and_qr_without_png_backend | 300 етикеток ≤ 60 с — вимір A-15 |
| AC-062 | td_mebli_shop | — | missing | — | [G2] сканування етикетки на комплектувальному листі (поле вводу коду + дія; `stock_barcode` — EE, не використовувати), «Запаковано» з користувачем, чужий код — повідомлення; FG: `group_feature_label_scan`; тест |
| AC-063 | td_mebli_sale, td_mebli_install | td_mebli_sale, td_mebli_install | done | td_mebli_install/tests/test_board_stage.py::test_board_shows_all_stages, test_wait_shipped_install_closed | — |
| AC-064 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_order_dates.py::test_stage_drag_needs_manufacturing_rights | [G1] звірити текст помилки з SPEC |
| AC-065 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_board_stage.py::test_wait_shipped_install_closed | [G3] перевірити позначку «Немає доплати <сума>» на картці дошки |
| AC-066 | td_mebli_sale | td_mebli_sale | partial | td_mebli_sale/tests/test_order_dates.py::test_workshop_shift_is_the_company_reason | [G1] `td_delay_reason` не має «Клієнт» (з версії зміни `td.mebli.order.change.reason='customer'`); групування списку за причиною; тест |
| AC-067 | td_mebli_sale, td_mebli_base | td_mebli_dashboard (лише картка) | partial | td_mebli_dashboard/tests/test_dashboard.py::test_cards_of_the_a_box | [G1] фільтр «Застряглі» на дошці замовлень (stored дата останньої зміни етапу + фільтр з `res.company.td_stuck_days`); [G3] константа `STUCK_DAYS` у дашборді → те саме поле (VP-10); тест зміни 5→10. ⚠ факт — лише картка дашборда; рядок ALLOCATION вірний, бракує коду в `td_mebli_sale` |
| AC-068 | td_mebli_mrp | td_mebli_mrp | done | td_mebli_mrp/tests/test_parts_view.py::test_production_shows_the_parts_of_its_bom; td_mebli_mrp/tests/test_order_bom.py::test_generate | — |
| AC-069 | td_mebli_mrp | td_mebli_mrp | done | td_mebli_mrp/tests/test_order_bom.py::test_workorder_load, test_capacity_from_calendar | — |
| AC-071 | td_mebli_shop | td_mebli_shop | partial | td_mebli_shop/tests/test_shop.py::test_pin_start_pause_quality_done, test_pin_errors_look_the_same | [G2] блок — 5 хв у пам'яті процесу; SPEC: 5 спроб → 15 хв, лічильник збережено (окремий курсор `registry.cursor()`, `odoo/orm/registry.py:1193`, поле на `hr.employee`); FG: `group_feature_kiosk`; тест |
| AC-072 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_shop.py::test_two_workers_through_the_kiosk | FG: `group_feature_kiosk` |
| AC-073 | td_mebli_shop | — | missing | — | [G2] дія «Брак» у кіоску: деталь + причина → МО на повторну деталь (origin — завдання), причина в журналі невідповідностей для дашборда (AC-121); FG: `group_feature_kiosk`; тест |
| AC-074 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_shop.py::test_pin_start_pause_quality_done | FG: `group_feature_quality` |
| AC-075 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_shop.py::test_pin_start_pause_quality_done | [G2] текст «Пройдіть крок якості: <назва>» звірити з uk.po |
| AC-076 | td_mebli_maint | td_mebli_maint | done | td_mebli_maint/tests/test_maintenance.py::test_breakdown_downtime_in_the_work_center_log, test_downtime_needs_a_work_center | — |
| AC-078 | td_mebli_attendance, td_mebli_bas | td_mebli_attendance | partial | td_mebli_attendance/tests/test_export.py::test_hours_by_employee, test_no_code_is_skipped_and_formulas_are_text | [G4] файл табеля є; бракує пакета BAS виду «табель» у `td_mebli_bas` і `hr.employee.td_bas_code` (ескалація A-13) |
| AC-079 | td_mebli_dashboard | td_mebli_dashboard | done | td_mebli_dashboard/tests/test_shop_board.py::test_board_figures, test_board_needs_manufacturing, test_board_only_selected_companies | [G3] FG: `group_feature_shop_board` |
| AC-080 | td_mebli_claim | td_mebli_claim | partial | td_mebli_claim/tests/test_claim.py::test_claim_on_the_order_and_remake | [G3] МО створюється на виріб; SPEC — на деталь (`td_part_id`), origin = номер рекламації; тест для деталі |
| AC-081 | td_mebli_claim | td_mebli_claim | partial | — | [G3] немає ні деталі, ні виробу → «Оберіть деталь або виріб для повторного виготовлення» (зараз інша помилка про BoM); тест |
| AC-083 | td_mebli_sale | td_mebli_sale (вкладка закупівель замовлення) | partial | — | [G1] екран «Затримані поставки» для комірника: рядки закупівель із запізненням і зачепленими замовленнями (`td_purchase_line_ids`), меню; тест |
| AC-085 | td_mebli_purchase | td_mebli_purchase | done | td_mebli_purchase/tests/test_price.py::test_price_above_the_average_of_earlier_purchases | [G2] VP-11 → `res.company.td_price_threshold_pct` (зараз `OVER_PCT = 5.0`) |
| AC-086 | td_mebli_purchase | td_mebli_purchase | code-no-test | — | [G2] тест: без історії — без позначки, підказка «немає історії» |
| AC-087 | td_mebli_purchase | td_mebli_purchase | done | td_mebli_purchase/tests/test_price_import.py::test_prices_go_to_the_vendor_pricelist, test_unhappy_rows_are_errors_not_zero, test_new_prices_keep_the_history | — |
| AC-088 | td_mebli_mrp | td_mebli_mrp | done | td_mebli_mrp/tests/test_wave2.py::test_short_board_suggests_and_uses_the_analog, test_analog_in_another_unit_kind_is_not_suggested | [G2] FG: `group_feature_analog` |
| AC-089 | td_mebli_migration | — | missing | — | [G4] новий `td_mebli_migration` (`tr/migration.md` §3): конвертори `scripts/convert_bas.py`, `convert_bazis.py` (формати — після зразків, ВП-1/ВП-3: лише каркас), звірка `td.mebli.migration.check(.line)`; тест звірки |
| AC-090 | td_mebli_migration | — | missing | — | [G4] стан «розбіжність» з різницею й записами-причинами, «звірено» лише при 0 або підписаному поясненні; тест |
| AC-091 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_kit_report.py::test_packing_list_prints_places; td_mebli_shop/tests/test_shop.py::test_incomplete_set_does_not_leave | — |
| AC-092 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_shop.py::test_incomplete_set_does_not_leave | — |
| AC-093 | td_mebli_shop | — | missing | — | [G2] «Створити дозамовлення» на рядку листа → МО на деталь з посиланням на замовлення, позначка «Дозамовлено» на `td.mebli.kit.line`; тест |
| AC-094 | td_mebli_shop | td_mebli_shop | done | td_mebli_shop/tests/test_kit_report.py::test_packing_list_prints_places | — |
| AC-096 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_day_plan.py::test_day_plan | — |
| AC-097 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_install.py::test_signed_act_is_read_only_and_amount_fixed, test_amount_of_the_signature_is_a_stored_field | [G3] чек-лист — з `res.company.td_act_checklist` (зараз текст у коді) |
| AC-098 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_install.py::test_signed_act_is_read_only_and_amount_fixed | [G3] додати тест гілки «Немає підпису клієнта» |
| AC-099 | td_mebli_install | td_mebli_install | done | td_mebli_install/tests/test_install.py::test_act_visible_as_its_visit, test_defect_visible_as_its_act | — |
| AC-100 | td_mebli_install | td_mebli_install | partial | — | [G3] є лише `photo_archive`; поле згоди покупця, помилка «Немає згоди покупця на публікацію фото», фільтр «Фотоархів»; тест |
| AC-101 | td_mebli_install | td_mebli_shop ⚠ | done | td_mebli_shop/tests/test_wave2.py::test_transfer_act_of_the_delivery | ⚠ звіт `td_mebli_shop.report_handover_act` у `td_mebli_shop`. Рекомендація: виправити рядок ALLOCATION (shop ⊂ depends install; перенесення міняє xmlid звіту — ризик). [G3] перевірити позначку юриста |
| AC-102 | td_mebli_install | td_mebli_install | partial | td_mebli_install/tests/test_payment.py::test_act_report_renders | [G3] у звіті акта немає позначки «Шаблон до перевірки юристом» (є лише в договорі й акті передачі) і її зняття за `td_legal_checked`; тест на вміст |
| AC-103 | td_mebli_install | td_mebli_install | partial | — | [G3] VP-15 `td_crew_base` (`final`/`stage`): зараз лише фінальний акт; тест «два виїзди» |
| AC-104 | td_mebli_install | td_mebli_install | partial | td_mebli_install/tests/test_install.py::test_signed_final_act_gives_the_crew_percent, test_piece_rate_of_the_operation_shared_by_time | [G3] VP-14 `td_crew_split` (`equal`/`time`): % бригаді ділиться лише порівну; `td_crew_pct` компанії як дефолт акта |
| AC-105 | td_mebli_install | td_mebli_install | partial | — | [G3] операції без розцінки відкидаються мовчки (`td_piece_rate > 0` у домені): підсумок «Без розцінки: N операцій» зі списком; тест |
| AC-106 | td_mebli_install | td_mebli_install | partial | td_mebli_install/tests/test_install.py::test_accountant_accrues_and_confirmed_is_fixed | [G3] правило «свої рядки» (`employee_id.user_id = user`) для монтажника/майстра — зараз доступу монтажника немає взагалі; скасування підтвердженого керівником з причиною; тест |
| AC-107 | td_mebli_install | td_mebli_install | partial | td_mebli_install/tests/test_install.py::test_accountant_accrues_and_confirmed_is_fixed | [G3] майстер додає премію/штраф лише працівникам своєї дільниці — правила немає; тест |
| AC-108 | td_mebli_install | td_mebli_install | code-no-test | — | [G3] SQL-обмеження `_reason_required` є; повідомлення «Вкажіть причину премії або штрафу»; тест |
| AC-109 | td_mebli_bas | — | missing | — | [G4] пакет «нарахування» з підтверджених `td.mebli.accrual`, `bas_state` (поле додає `td_mebli_bas` через `_inherit`), зміна переданих — лише сторно; тест |
| AC-110 | td_mebli_claim | td_mebli_claim | partial | td_mebli_claim/tests/test_claim.py::test_claim_on_the_order_and_remake | [G3] «Прострочено» рахується від `schedule_date`; SPEC — понад `res.company.td_claim_overdue_days` (VP-13); тест |
| AC-111 | td_mebli_claim | td_mebli_claim | partial | — | [G3] гарантія — `ir.config_parameter` `td_mebli_claim.warranty_months` (24 для всіх) → `product.category.td_warranty_months` [G0]; не задано — «Гарантійний строк не задано», рішення сервісу; тест |
| AC-112 | td_mebli_claim | td_mebli_claim | done | td_mebli_claim/tests/test_claim.py::test_after_warranty_the_customer_pays | — |
| AC-113 | td_mebli_helpdesk | — | ee-bridge | — | [G4] модуль-міст (маніфест `auto_install`, `depends: td_mebli_claim, helpdesk`), лише код; поля/моделі Helpdesk не звірено (EE недоступна) |
| AC-114 | td_mebli_cost | td_mebli_cost | partial | td_mebli_cost/tests/test_cost.py::test_plan_and_actual | [G3] у факті немає рядка «порізка» (закупівлі послуги порізки замовлення) — `depends` + `td_mebli_cutting` (`tr/00-architecture.md`); тест |
| AC-115 | td_mebli_cost, td_mebli_base | — | missing | — | [G3] `groups=` (finance/director) на полях `td_cost_*`, `td_margin_fact*` і меню; тест невидимості для менеджера |
| AC-116 | mrp, td_mebli_mrp (A-12 з модулем A-11) | td_mebli_mrp | done | td_mebli_mrp/tests/test_wave2.py::test_order_bom_warns_about_overconsumption | [G3] фільтр «Перевитрата» у звіті S-11 (`td_mebli_cost`) |
| AC-118 | td_mebli_sale | td_mebli_sale | done | td_mebli_sale/tests/test_order_change.py::test_change_keeps_before_and_after | Причина «Клієнт» → дошка — AC-066 |
| AC-119 | td_mebli_sale | — | missing | — | [G1] після відправлення в розкрій — лише «Дозамовлення»; блок змін деталей повідомленням AC-052 (залежить від `mrp.bom.td_cut_version` [G2]); тест |
| AC-120 | td_mebli_sale | — | missing | — | [G1] «Надіслати зміну на підпис»: портальна сторінка версії зміни й підпис (стандартний підпис порталу `sale`), стан «Підписано клієнтом»; FG: `group_feature_change_sign`; тест (портальний контролер — найбільший обсяг у G1) |
| AC-121 | td_mebli_dashboard | td_mebli_dashboard | partial | td_mebli_dashboard/tests/test_dashboard.py::test_cards_of_the_a_box; td_mebli_demo/tests/test_dashboard_data.py::test_finance_role_opens_every_card | [G3] 11 карток A є; 12-та «Невідповідності якості» для B/C (за `group_feature_quality`) відсутня; тест |
| AC-122 | td_mebli_dashboard, td_mebli_base | td_mebli_dashboard | done | td_mebli_dashboard/tests/test_dashboard.py::test_access_is_limited_to_the_director | ⚠ група `td_mebli_dashboard.group_td_mebli_director`, ТР — `td_mebli_base.group_director`. Рекомендація: у цій хвилі лишити групу в дашборді (міграція xmlid і користувачів — окремо, AC-N.04) і позначити це в ALLOCATION |
| AC-123 | td_mebli_dashboard | td_mebli_dashboard | code-no-test | — | [G3] тест на порожніх даних: 0 / «Немає даних», без ділення на нуль |
| AC-124 | td_mebli_notify | td_mebli_notify | done | td_mebli_notify/tests/test_notify.py::test_briefing, test_briefing_only_companies_of_the_owner, test_briefing_counts_visits_of_a_project_without_company | [G1] VP-10/VP-13 читати з полів компанії |
| AC-125 | td_mebli_notify | td_mebli_notify | partial | — | [G1] шаблон брифінгу без відхилень показує розділи з «No downtime.»; потрібне одне повідомлення «Відхилень немає»; тест |
| AC-126 | td_mebli_shopfloor | — | ee-bridge | — | [G4] міст `td_mebli_shopfloor` (`td_mebli_shop` + `mrp_workorder`), лише код |
| AC-127 | td_mebli_quality | — | ee-bridge | — | [G4] міст `td_mebli_quality` (`td_mebli_shop` + `quality_control`), лише код |
| AC-128 | td_mebli_fsm, td_mebli_planning | — | ee-bridge | — | [G4] мости `td_mebli_fsm`, `td_mebli_planning` (`td_mebli_install` + `industry_fsm` / `planning`), лише код |
| AC-129 | td_mebli_sign | — | ee-bridge | — | [G4] міст `td_mebli_sign` (`td_mebli_install` + `sign`), лише код |
| AC-130 | 6 мостів | — | ee-bridge | — | [G4] у CE перевіряється: тест, що жоден міст не встановлено в базі CE, і перевірка маніфестів (`auto_install: True`, у `depends` EE-модуль); установка на EE — MANUAL (ВП-4) |
| AC-131 | td_mebli_cutting | td_mebli_cutting (лише точка входу) | partial | — | [G2] `_td_apply_result(payload)` є, але лише для імітації; майстер «Імпортувати результат» (файл програми розкрою → payload, `result_source='imported'`, деталь не з завдання — помилка); формат файлу — відкрите питання; тест |
| AC-132 | td_mebli_claim | — | missing | — | [G3] «Запланувати виїзд» з рекламації: `project.task` у проєкті монтажів з посиланням на рекламацію й адресою (у `depends` `td_mebli_claim` додати `project`); видно в календарі й денному плані; тест |
| AC-133 | td_mebli_shop | — | missing | — | [G2] звіт «Наряд на замовлення» (МО: операції, деталі з QR, поля відміток) + дія «Зроблено заднім числом» з причиною (рядок часу на інтервал, дата в майбутньому — помилка); тест |
| AC-134 | td_mebli_install | — | missing | — | [G3] QWeb-звіт «Відомість нарахувань» за працівниками й видами з причинами, лише підтверджені; тест рендеру |

### Нефункціональні (AC-N.xx)

| AC | модуль (ALLOCATION) | модуль (факт) | стан | тест | що зробити |
|---|---|---|---|---|---|
| AC-N.01 | `i18n/uk.po` усіх `td_mebli_*` (A-11) | 15 модулів зрізу | partial | — | `uk.po` є в усіх 15; нові модулі (base, bas, migration, multico, мости) — додати; повноту перекладу перевірить A-14 |
| AC-N.02 | td_mebli_sale, td_mebli_mrp, td_mebli_shop | — | code-no-test | — | функціональні тести обсягу (300 деталей, 300 етикеток); вимір часу — A-15/A-16 |
| AC-N.03 | l10n_ua, account | — | — (A-12) | — | конфіг; код не потрібен |
| AC-N.04 | `migrations/19.0.1.1.0/` модулів зрізу | — | missing | — | версії зрізу `19.0.1.0.0`, `migrations/` немає. Кожна група піднімає версію своїх модулів до `19.0.1.1.0`; перенесення параметрів зрізу — `post_init_hook` `td_mebli_base` (base новий, `migrations/` у нього не спрацює); xmlid груп поки не переносимо |
| AC-N.05 | інфраструктура | — | поза A-11 | — | C-00 / хостинг |
| AC-N.06 | td_mebli_base | — | missing | — | [G0] вільний шрифт з кирилицею в `static/fonts/`, `@font-face` у `web.report_assets_common` (`addons/web/__manifest__.py:256`), клас `td_mebli_report`; звіти зрізу (договір, акти, етикетки, комплект) отримують клас — кожна група у своїх модулях; тест рендеру PDF |
| AC-N.07 | td_mebli_base (feature-групи) | — | missing | — | [G0] 11 груп `group_feature_*` і галочки `res.config.settings` з `implied_group` (зразок — `addons/account/models/res_config_settings.py:80`); `groups=` на меню/кнопках функцій B — кожна група у своїх модулях (позначка FG) |

## Підсумок за станами

| Стан | AC (функціональні, 125 рядків: 119 «код» + 5 «A-12 з модулем A-11» + AC-043) | NFR |
|---|---|---|
| done | 49 | 0 |
| code-no-test | 8 | 1 (N.02) |
| partial | 36 | 1 (N.01) |
| missing | 26 | 3 (N.04, N.06, N.07) |
| ee-bridge | 6 | — |
| поза A-11 | — | 2 (N.03, N.05) |

Окремо: із 49 «done» ще 12 (AC-011, 012, 020, 026, 059, 072, 074, 079, 085, 088, 097, 124) потребують заміни константи/параметра зрізу на поле `res.company.td_*` (VP-06, -07, -09, -10, -11, -12, -13, `contract_mode`) або feature-групи (FG) — без цього A-12 не застосує VP (ескалація A-12, CFG-readback).
Модулі з ALLOCATION, яких немає: `td_mebli_base`, `td_mebli_bas`, `td_mebli_multico`, `td_mebli_migration`, 6 мостів EE. Модулі `td_mebli_notify`, `_maint`, `_attendance` у дереві вже є (у звітах A-12/A-13 їх ще не було).

## План збірки

Принцип: кожен модуль належить рівно одній групі — паралельні виконавці не правлять ті самі файли. `td_mebli_demo` не входить у групи: підлаштування демо (параметри, `td_bas_state`) — короткий завершальний крок після G1–G4.

### G0 — основа `td_mebli_base` (першою, послідовно, 1 виконавець)
- **AC:** AC-018 (поле й група), AC-N.06, AC-N.07; поля VP для AC-020, -031, -033/034, -043, -059, -067, -085, -097, -103/104, -110, -111, -124.
- **Модулі:** новий `td_mebli_base`; у зрізі — лише рядок `depends` у маніфестах кореневих модулів `td_mebli_mrp`, `td_mebli_purchase`, `td_mebli_ua`, `td_mebli_maint`, `td_mebli_attendance` (решта отримує base транзитивно).
- **Нове:** поля `res.company` за `tr/td_mebli_base.md` §1 (+ `td_cutting_mode` для VP-09 — уточнити в ТР), `product.category.td_warranty_months`, розділ «Меблі» в `res.config.settings` (`related='company_id.…', readonly=False`), привілей «Меблі», групи `group_finance`, `group_margin_view`, 11 `group_feature_*`, шрифт PDF, `post_init_hook`: перенесення `td_mebli_sale.contract_mode` (`work`→`contract`), `td_mebli_install.payment_control`, `td_mebli_claim.warranty_months` у поля. Тести полів, синхронізації `group_margin_view`, hook.
- **Не робити в G0:** не переносити групи зрізу (`group_td_mebli_measurer`, `group_td_mebli_director`) і правила інших модулів.

### G1 — продаж, замір, повідомлення, ФОП (паралельно з G2, G3 після G0)
- **AC:** 003, 005, 006, 007, 008, 010, 014, 016, 018 (види), 030, 031, 033, 034, 035, 036 (`td.mebli.order.change`, measure), 043, 064, 066, 067 (фільтр дошки), 083, 119, 120, 124, 125.
- **Модулі:** `td_mebli_sale`, `td_mebli_measure`, `td_mebli_notify`, новий `td_mebli_multico`.
- **Нове:** поля `sale.order.td_install_company_id`/`td_parent_order_id`/`td_install_order_ids` (multico); `td_delay_reason` += `customer`; stored дата зміни етапу для «Застряглих»; стан «Не перевірено» техніки; шаблон «Запис на замір»; портальний підпис зміни.
- **Залежності:** AC-119 — після поля `mrp.bom.td_cut_version` з G2 (робити останнім у G1).

### G2 — специфікація, розкрій, цех, закупівлі (паралельно після G0)
- **AC:** 011, 012 (FG), 026 (VP-09), 028, 036 (cutting, kit, quality), 045–050, 052, 054, 056–060, 062, 071–075 (FG/тексти), 085, 086, 088, 093, 131, 133.
- **Модулі:** `td_mebli_mrp`, `td_mebli_cutting`, `td_mebli_shop`, `td_mebli_purchase`.
- **Нове:** `td.mebli.import.template`; `mrp.bom.td_cut_version`; `td.mebli.cutting.job.bom_version`, `sent_date`; майстри «Імпортувати результат», «Підібрати обрізок»; кіоск «Брак» (МО на деталь, причина); `td.mebli.kit.line` стан «Дозамовлено» + сканування коду; звіт «Наряд на замовлення»; лічильник PIN на `hr.employee`.
- **Залежності:** дає G1 поле для AC-119; дає G3 журнал браку для 12-ї картки AC-121.

### G3 — монтаж, рекламація, собівартість, дашборд (паралельно після G0)
- **AC:** 020, 021, 036 (act, defect), 065, 067 (картка), 079 (FG), 080, 081, 097–108, 110–112, 114–116 (фільтр), 121–123, 132, 134; ALLOCATION-рядок AC-101.
- **Модулі:** `td_mebli_install`, `td_mebli_claim`, `td_mebli_cost`, `td_mebli_dashboard` (`td_mebli_maint` — без змін).
- **Нове:** `td.mebli.pay.mark`; поле згоди на фото в акті; параметри поділу/бази % бригаді; правила «свої нарахування», «своя дільниця»; звіт «Відомість нарахувань»; `repair.order` → задача-виїзд; `groups=` на собівартості; 12-та картка якості.
- **Залежності:** дає G4 `td.mebli.pay.mark` (AC-042); 12-та картка AC-121 — після «Браку» з G2 (або читає лише `td.mebli.quality.check`).

### G4 — інтеграції й мости EE (після G0; AC-042 — після G3)
- **AC:** 037, 038, 039–042, 078, 089, 090, 109, 113, 126–130.
- **Модулі:** `td_mebli_ua`, `td_mebli_attendance`, нові `td_mebli_bas`, `td_mebli_migration`, `td_mebli_shopfloor`, `td_mebli_quality`, `td_mebli_fsm`, `td_mebli_planning`, `td_mebli_helpdesk`, `td_mebli_sign`.
- **Нове:** моделі обміну `td.mebli.bas.channel/.batch/.log`, `td_bas_code` (partner, product, employee; потрібні й A-13), `account.move.td_bas_state`, `td.mebli.accrual.bas_state` (через `_inherit` у `td_mebli_bas`); прибрати імітацію `sale.order.td_bas_state` з `td_mebli_ua` (R-06) і замінити compute у `td_mebli_bas`; `td.mebli.migration.check(.line)`; кнопка «Оновити ціни за курсом», активність про збій НБУ.
- **Порядок усередині:** ua → bas (без оплат) → migration → bas-оплати (після G3) → мости.

**Порядок:** G0 → (G1 ∥ G2 ∥ G3 ∥ G4-частина без оплат) → G1: AC-119, G3: 12-та картка, G4: AC-042 → демо → A-14.

## Нові модулі: структура (мінімальний ризик)

| Модуль | `depends` | Вміст | Що НЕ виносимо з зрізу (і чому) |
|---|---|---|---|
| `td_mebli_base` | `base_setup`, `mail`, `hr` | `models/res_company.py` (поля VP §1), `models/product_category.py`, `models/res_config_settings.py` (+ feature-галочки), `security/td_mebli_security.xml` (привілей, `group_finance`, `group_margin_view`, `group_feature_*`), `views/res_config_settings_views.xml`, `static/fonts/` + `report_assets.xml`, `hooks.py` (`post_init_hook` перенесення параметрів), `i18n/uk.po`, `tests/` | Групи ролей зрізу (замірник у `td_mebli_measure`, керівник у `td_mebli_dashboard`) і `ir.rule` інших моделей: перенесення змінює xmlid, ламає права користувачів і демо; робимо пізніше одним кроком з `migrations/` (AC-N.04). Поля параметрів `res.config.settings` у `td_mebli_sale`/`td_mebli_install` — видалити в G1/G3 після hook |
| `td_mebli_bas` | `td_mebli_install`, `td_mebli_attendance`, `account` | `models/bas_channel.py`, `bas_batch.py`, `bas_log.py`, `account_move.py`, `res_partner.py`/`product.py`/`hr_employee.py` (`td_bas_code`), `sale_order.py` (`td_bas_state` compute), `accrual.py`; `data/ir_cron.xml`; `security/` (finance); меню «Облік → Обмін з BAS»; формат пакета — JSON-схема-чернетка до ВП-1 | транспорт `http` і схема BAS — лише каркас до узгодження з франчайзі (ВП-1) |
| `td_mebli_multico` | `td_mebli_install` | `models/sale_order.py` (3 поля + `action_confirm`), `views/sale_order_views.xml` (`groups="base.group_multi_company"`), тести на 2 компаніях | — |
| `td_mebli_migration` | `td_mebli_sale`, `base_import` | `models/migration_check.py` (+ `.line`), `views/`, `security/`, `scripts/convert_bas.py`, `scripts/convert_bazis.py` (каркас; формати після зразків, B-06) | конвертори не запускаються в Odoo — це CLI для B-06 |
| мости EE (6) | модуль ядра + EE-додаток; `auto_install: True` (зразок `addons/sale_mrp/__manifest__.py:24`) | маніфест, мінімальні `_inherit` за `tr/ee-bridges.md`, `groups=`-приховування td-меню; у кожного `README.md` «не перевірено на EE» | моделі/поля EE не звірено (ВП-4): код без запуску, тест лише AC-130 у CE |

## Ризики й розбіжності SPEC ↔ код
1. **Ключі параметрів:** `td_mebli_sale.contract_mode` = `work/sale`, а схема `answers.yaml` — `contract/sale/unset`. Default `work` суперечить AC-034 (без режиму має бути помилка). Перенесення в `res.company.td_contract_mode` змінює поведінку демо: демо мусить задати режим.
2. **AC-006:** група замірника зрізу включає «Продажі: власні документи», тож замірник бачить ціни. Виправлення урізає права, які зараз використовує майстер запису.
3. **Гарантія AC-111:** зріз дає 24 міс. глобально, SPEC — строк категорії, а до юриста порожньо. Демо `wave2.py` спирається на 24 міс.
4. **Feature-груп немає:** у коробці A зараз видно функції B (кіоск, обрізки, табло, аналоги, НБУ). Профіль light (AI-A10-05) без них неможливий.
5. **Модулі не на своєму місці:** AC-101 (звіт у shop), AC-122 (група керівника в dashboard), AC-036 (правила мусять жити в модулях-власниках), AC-067 (є лише картка дашборда). Пропозиція: виправити рядки ALLOCATION, код не переносити.
6. **Розбіжності текстів і числових значень SPEC:** PIN 5 хв проти 15 хв зі збереженим лічильником; номер заміру `ЗМ-` проти `ЗМ/РРРР/NNNN`; нагадування за 3 дні проти 2 (VP-07); тексти помилок англійською відрізняються від SPEC — звіряти через `uk.po`.
7. **AC-050 (AI-мапінг):** зовнішній виклик з даними файлу. Потрібне рішення DATA_POLICY і постачальник. Пропоную FG вимкнено за замовчуванням і заглушку в тестах.
8. **AC-131, AC-089, AC-039:** формати файлів програми розкрою, BAS і БАЗИС невідомі (ВП-1, ВП-3). Можна зробити лише каркас із чернетковим форматом, тож A-14 матиме WARN.
9. **Мости EE:** код без запуску. AC-113 і AC-126…129 на CE не перевіряються (MANUAL).
10. **AC-N.04:** у зрізі немає `migrations/`. Поля, додані до наявних моделей, ставляться оновленням модуля. Перенесення xmlid груп відкладено, і це потрібно зафіксувати в ALLOCATION/ТР.
