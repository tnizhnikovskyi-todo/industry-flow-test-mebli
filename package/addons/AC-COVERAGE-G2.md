# AC-COVERAGE — група G2 (специфікація, розкрій, цех, закупівлі)

Модулі: `td_mebli_mrp`, `td_mebli_cutting`, `td_mebli_shop`, `td_mebli_purchase` — версія `19.0.1.1.0` (migrations/ не потрібні: поля лише додано, xmlid не перейменовано; єдине прибране — `selection_add` `td_delay_reason='cutting'` з `td_mebli_cutting`, див. G2-6).
Прогін: база `test-mebli-a11g2-r5`, `-i td_mebli_mrp,td_mebli_cutting,td_mebli_shop,td_mebli_purchase --test-tags /td_mebli_mrp,/td_mebli_cutting,/td_mebli_shop,/td_mebli_purchase` — результат у розділі «Прогін» нижче.
Тексти помилок — дослівно за SPEC через `i18n/uk.po` (англійське джерело в коді, тести звіряють англійський текст повністю `^…$`).

## Стан AC

| AC | модуль | стан | тест | що зроблено / примітка |
|---|---|---|---|---|
| AC-028 | td_mebli_cutting | done | td_mebli_cutting/tests/test_g2_cutting.py::test_ac_028_sent_version_date_and_fixed_file | поля `bom_version`, `sent_on`, `sent_by` (readonly, ставить «Передати на розкрій»/«дистриб'ютору»); `export_attachment_id` після відправлення не змінюється («…make a new cutting job»); у файлі деталей — колонка `code` |
| AC-045 | td_mebli_mrp | done | td_mebli_mrp/tests/test_g2_spec.py::test_ac_045_replace_is_the_default_and_append_adds, test_ac_045_board_lines_from_the_parts_and_chatter | режим `replace` (типово) / `append`; після імпорту рядки плити й кромки перераховано з деталей (`_td_recompute_component_lines`, позначка «З деталей»); у чаті — файл (вкладення), кількість, режим |
| AC-046 | td_mebli_mrp | done | test_g2_spec.py::test_ac_046_no_width_column_nothing_written | обов'язкові колонки: деталь, довжина, ширина, кількість, матеріал (TR §8 п.1); «У файлі не знайдено колонок: Ширина. Перевірте заголовки або задайте мапінг»; у діалозі — попередження й ручне зіставлення |
| AC-047 | td_mebli_mrp | done | test_g2_spec.py::test_ac_047_unknown_material_blocks_until_mapped | матеріал шукається в довіднику плит (`default_code`/назва), не «перша плита»; рядки «Рядок N: «код» — Матеріал не знайдено»; «Імпортувати» сховано й заблоковано, доки не зіставлено (таблиця «Матеріали для зіставлення») або не прибрано |
| AC-048 | td_mebli_mrp | done (функц.) | test_g2_spec.py::test_ac_048_three_hundred_parts | 300 деталей одним `create`; межа 30 с у тесті — функціональна; вимір на еталонному стенді — A-15 (NFR-3) |
| AC-049 | td_mebli_mrp | done | test_g2_spec.py::test_ac_049_manual_mapping_saved_as_template | модель `td.mebli.import.template` (назва, компанія, підпис заголовків, `mapping_json`, active), меню «Виробництво → Налаштування → Шаблони імпорту», правило компанії; ручне зіставлення колонок у діалозі + «Зберегти мапінг як шаблон»; наступний файл — за шаблоном без ручного кроку |
| AC-050 | td_mebli_mrp | done (каркас) | test_g2_spec.py::test_ac_050_ai_hint_off_by_default_no_call, test_ac_050_ai_hint_on_sends_headers_and_ten_rows | виклик лише при `group_feature_ai_mapping` **і** заданому `td_mebli_mrp.ai_mapping_url` (налаштування в блоці функцій B); назовні — заголовки + ≤ 10 рядків; підказка — позначені колонки + банер, не імпорт; збій/вимкнено — ручний мапінг без помилки. Тести підміняють `_td_ai_request`, реального виклику немає. Протокол постачальника — MANUAL (G2-1) |
| AC-052 | td_mebli_mrp (+ cutting) | done | test_g2_spec.py::test_ac_052_parts_of_a_sent_specification_are_locked; test_g2_cutting.py::test_ac_028_… | **поле `mrp.bom.td_cut_version`** (int, readonly, 0 — не відправлено; +1 при кожному відправленні, `mrp.bom._td_mark_sent_to_cutting()`); `td.mebli.part.locked`; `create`/`write`/`unlink` деталі відправленої специфікації — «Специфікацію відправлено в розкрій (версія N) — зміна лише дозамовленням»; кнопка «Імпорт деталей» прихована |
| AC-054 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_054_manufacturing_order_without_parts | «У виробничому замовленні <номер> немає деталей розкрою», завдання не створюється (раніше МО без деталей мовчки відкидалось) |
| AC-056 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_056_no_measurement_warns_and_sends | `td_measure_missing`; при відправленні — запис у чаті «Замір не заповнено — перевірку пропущено», банер на формі (чернетка); не блокує |
| AC-057 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_057_batch_of_three_orders_of_one_decor | >1 МО — лише з `group_feature_cutting_batch` (інакше помилка); у списку деталей завдання — колонки МО й замовлення (`td.mebli.part.td_production_id`, `td_order_name`); етикетка МО (AC-061) уже має замовлення |
| AC-058 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_058_different_boards_in_one_job | «В одному завданні розкрою — лише один матеріал плити»: у пакеті кількох МО набір плит кожного МО має збігатися (G2-3) |
| AC-059 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_059_minimum_from_the_company_and_box_a_keeps_no_offcuts; test_cutting_done.py::test_reserve_and_offcuts | default `min_offcut_mm` ← `res.company.td_min_offcut_mm` (VP-12); ділові обрізки-партії лише з `group_feature_offcut` (у коробці A залишки — відхід); меню «Ділові обрізки» — за FG |
| AC-060 | td_mebli_cutting | done | test_g2_cutting.py::test_ac_060_pick_an_offcut_for_a_part | кнопка «Підібрати обрізок» на деталі завдання (FG offcut) → майстер `td.mebli.offcut.pick`: вільні обрізки того самого матеріалу, на складі, без резерву, ≥ деталі з поворотом; вибір — стандартний резерв партії на рух матеріалу МО деталі, запис у чаті |
| AC-062 | td_mebli_shop | done | td_mebli_shop/tests/test_g2_shop.py::test_ac_062_scan_a_label_packs_the_line | кнопка «Сканувати етикетки» на замовленні (FG `label_scan`) → майстер `td.mebli.kit.scan`: код етикетки (сканер вводить у поле) → «Запаковано» з користувачем; чужий/невідомий — «Етикетка не належить цьому замовленню», нічого не змінено. `stock_barcode` (EE) не використано; камера телефона — MANUAL (G2-5) |
| AC-071 | td_mebli_shop | done | test_g2_shop.py::test_ac_071_five_wrong_pins_lock_for_15_minutes_in_the_database; test_shop.py::test_pin_errors_look_the_same | `hr.employee.td_pin_fail_count`, `td_pin_locked_until` (`hr.group_hr_user`); кожна невдача пишеться окремим курсором `registry.cursor()` (переживає відкат запиту, перезапуск і кілька воркерів); 5 поспіль → блок 15 хв, «Працівника заблоковано до HH:MM»; невдача — «Невірний PIN»; успіх скидає лічильник. Меню «Планшет цеху» — FG `kiosk` |
| AC-073 | td_mebli_shop | done | test_g2_shop.py::test_ac_073_scrap_makes_a_repeat_part_and_a_non_conformity | дія «Брак» у кіоску (FG `kiosk`): деталь + причина → МО «Повторна деталь» (специфікація з однієї деталі, origin «МО / операція», причина в чаті) + рядок журналу невідповідностей `td.mebli.quality.check` (`kind='scrap'`, `result='fail'`, `note`=причина, `repeat_production_id`); крок якості не блокує |
| AC-085 | td_mebli_purchase | done | td_mebli_purchase/tests/test_price.py::test_ac_085_mark_above_history_with_the_percent, test_ac_085_threshold_from_the_company | позначка «Вище історії +8 %» (`td_history_note`) у рядку закупівлі й у звіті; фільтр «Вище історії» є; показник дашборда — G3 |
| AC-086 | td_mebli_purchase | done | test_price.py::test_ac_086_no_history_no_mark_and_a_hint | без історії: позначки немає, колонка історії порожня, підказка «немає історії», підтвердження без помилки |
| AC-093 | td_mebli_shop | done | test_g2_shop.py::test_ac_093_additional_order_of_a_missing_part | кнопка «Створити дозамовлення» на рядку листа → МО на деталь (origin — замовлення), `reorder_production_id` «Дозамовлено», запис у чаті замовлення; рядок без деталі (фурнітура) — помилка |
| AC-131 | td_mebli_cutting | partial (каркас + MANUAL) | test_g2_cutting.py::test_ac_131_import_of_the_cutting_result, test_ac_131_part_of_another_job_writes_nothing | кнопка «Імпортувати результат» → майстер `td.mebli.cutting.result.import`: CSV за описом SPEC (аркуш, деталь, позиція, обрізки; колонки — у коді й на формі) → аркуші, розміщення, обрізки, відхід %, `result_source='imported'` «Імпорт з програми розкрою», стан «Результат»; чужа деталь — «Деталь <код> не належить завданню», нічого не записано. **MANUAL:** формат файлу реальної програми розкрою невідомий (ВП-1) — конвертер під неї після зразка файлу |
| AC-133 | td_mebli_shop | done | test_g2_shop.py::test_ac_133_paper_sheet_and_done_afterwards | звіт «Наряд на замовлення» на МО (клас `td_mebli_report`; операції з полями відміток, деталі з QR і кодами етикеток) + кнопка «Зроблено заднім числом» у списку робочих завдань МО → рядок часу на інтервал з причиною, завдання «Зроблено», причина в чаті МО; майбутня дата — «Дата завершення не може бути в майбутньому». PDF через wkhtmltopdf у тесті не друкується (HTML-рендер) |

### Feature-групи (AC-N.07) і суміжні AC групи

| Що | Де | Стан |
|---|---|---|
| `group_feature_ai_mapping` | колонка «Пропозиція AI» і виклик (AC-050) | done |
| `group_feature_cutting_batch` | >1 МО у завданні (AC-057) | done (сервер) |
| `group_feature_offcut` | меню «Ділові обрізки», кнопка «Підібрати обрізок», створення партій-обрізків при «Підтвердити» | done |
| `group_feature_kiosk` | меню «Планшет цеху», дія «Брак»; меню «Перевірки якості» (kiosk або quality) | done |
| `group_feature_quality` | кнопка «Якість» планшета, поле «Крок якості» операції (AC-074) | done (UI) |
| `group_feature_label_scan` | кнопка «Сканувати етикетки» (AC-062) | done |
| `group_feature_analog` | колонка й кнопка «Взяти аналог» у МО (AC-088) | done (UI) |
| `group_feature_configurator` | поля розмірів рядка продажу (AC-011/012) — це `td_mebli_sale` (G1) | хвіст G1 |
| AC-026 (VP-09) | `td.mebli.cutting.job.td_cutting_mode` (related компанії); кнопка «Передати на розкрій» прихована при `distributor` | done, тест test_ac_026_distributor_mode_is_visible_on_the_job |
| AC-036 (частина G2) | `ir.rule` компанії: `td.mebli.cutting.job` (компанія — з МО), `td.mebli.kit.line` (+ `company_id` related store), `td.mebli.quality.check` (+ `company_id`), `td.mebli.import.template` | code-no-test (тест на 2 компаніях не писали); `td.mebli.part.company_id` (R-03) — не додано |
| AC-072 / AC-075 | тексти за SPEC: «Завдання вже виконує <А>. Двоє на одному завданні з одного планшета — поставте паузу або оберіть інше завдання», «Пройдіть крок якості: <назва>» | done (тест test_shop.py::test_two_workers_through_the_kiosk оновлено) |

## Модель даних (нові поля й моделі G2)

| Модель / поле | Модуль | Аналог у стандарті CE / чому td_ |
|---|---|---|
| `mrp.bom.td_cut_version` (int) | td_mebli_mrp | немає: стандарт не має «відправлено в розкрій»; `version` є лише в PLM (EE) |
| `td.mebli.part.locked` (compute) | td_mebli_mrp | — (від `td_cut_version`) |
| `td.mebli.import.template` (name, company_id, header_signature, mapping_json, active) | td_mebli_mrp | `base_import.mapping` зберігає мапінг лише для стандартного імпорту моделі, не для майстра деталей |
| `td.mebli.spec.import.mode/template_id/column_ids/missing_columns/unknown_lines/material_map_ids/template_name/ai_note`; transient `td.mebli.spec.import.column`, `.material` | td_mebli_mrp | майстер зрізу |
| `res.config.settings.td_ai_mapping_url` → `ir.config_parameter td_mebli_mrp.ai_mapping_url` | td_mebli_mrp | — (постачальник моделі не обраний, AI-A08-13) |
| `td.mebli.cutting.job.bom_version`, `sent_on`, `sent_by`, `td_cutting_mode` (related), `td_measure_missing` (compute) | td_mebli_cutting | — |
| `td.mebli.part.td_production_id`, `td_order_name` (compute) | td_mebli_cutting | — |
| transient `td.mebli.offcut.pick`, `td.mebli.cutting.result.import` | td_mebli_cutting | резерв — стандартний `stock.move._update_reserved_quantity` за партією |
| `hr.employee.td_pin_fail_count`, `td_pin_locked_until` | td_mebli_shop | `hr_attendance` має PIN, але без лічильника/блокування |
| `td.mebli.quality.check.kind`, `part_id`, `repeat_production_id`, `company_id` | td_mebli_shop | `quality_control` — EE |
| `td.mebli.kit.line.company_id`, `reorder_production_id` | td_mebli_shop | — |
| `product.product` `td_mebli_shop.product_td_repeat_part` «Повторна деталь» (дані) | td_mebli_shop | стандартний `mrp` брак (`stock.scrap`) списує, але не створює повторну деталь |
| transient `td.mebli.kit.scan`, `td.mebli.workorder.backdate`; звіт `td_mebli_shop.action_report_workorder_sheet` | td_mebli_shop | `stock_barcode` — EE; паперовий наряд у стандарті CE — лише «Work Order» без деталей і QR |
| `purchase.order.line.td_history_note` (compute) | td_mebli_purchase | — |

## Рішення AI з ризиком (G2)

| # | Рішення | Ризик |
|---|---|---|
| G2-1 | AC-050: AI-мапінг вимкнено за замовчуванням: виклик лише при FG `ai_mapping` **і** заданій адресі постачальника (`td_mebli_mrp.ai_mapping_url`); протокол — POST JSON `{headers, rows≤10, fields}` → `{mapping: {поле: № колонки}}` (вигаданий каркас) | реальний постачальник і підстава обробки за DATA_POLICY не обрані; протокол доведеться адаптувати; рядки файлу можуть містити назви, які людина вважатиме даними клієнта — перевірити на пілоті |
| G2-2 | AC-052: блокування деталей — `td_cut_version > 0`, скасування завдання **не** знімає блок (файл уже пішов у розкрій) | технолог, що скасував помилково відправлене завдання, не може правити деталі — лише дозамовлення або менеджер через контекст `td_cut_unlock` (лише код) |
| G2-3 | AC-058: «один матеріал плити» — для пакета кількох МО набори плит МО мають збігатися (одне МО з корпусом + фасадом + ДВП дозволене: завдання одного МО ріже всі свої плити, як у зрізі) | буквальне «одна плита на завдання» розбило б кожне МО на 3 завдання; якщо власник хоче буквально — переробити на завдання «по декору» |
| G2-4 | AC-057/058 перевіряються для користувача; `env.su` (скрипти демо, міграції) не перевіряється | демо `td_mebli_demo/scenario.py` (крок 9) і `showcase.py` об'єднують МО різних декорів і з FG вимкненими — під суперкористувачем пройдуть, але це не та поведінка, яку бачить технолог (хвіст демо) |
| G2-5 | AC-062: сканування — поле вводу коду (сканер-клавіатура + Enter) у майстрі; віджет камери (`barcodes`) не підключено | сканування камерою телефона — MANUAL, перевірити на пілоті; QR етикетки МО (`<МО>-NN`) не сканується в лист (лист має коди `<замовлення>-<місце>-<№>`) |
| G2-6 | Прогноз дати при порізці в дистриб'ютора переведено на хук G1 `sale.order._td_distributor_date()` + причина `distributor` (G1); власні `_td_shop_date`/`selection_add 'cutting'` прибрано; `purchase.order.line._td_sale_orders()` доповнено замовленнями завдання (перерахунок при зміні дати закупівлі) | G1 ще правив `td_mebli_sale`: якщо назва хука зміниться — тест test_distributor впаде; дашборд (G3, `dashboard.py:83`) рахує ключ `'cutting'` — має стати `'distributor'` |
| G2-7 | AC-073/093: МО на одну деталь — на сервісний продукт «Повторна деталь» зі специфікацією з однієї деталі; створюється від імені системи (`sudo`), бо кіоск і комплектувальник не мають прав виробництва | собівартість повторної деталі не потрапляє в замовлення автоматично (лише origin); правило «хто може створити МО» — через кнопку, не через права |
| G2-8 | AC-071: блокування — після 5-ї невдачі (5-та отримує «Невірний PIN», наступна — «заблоковано до HH:MM»); лічильник скидається при блокуванні й успіху | окремий курсор: якщо основний запит уже тримає блокування рядка працівника, запис лічильника чекатиме (у потоці кіоску працівника до перевірки PIN не пишемо) |
| G2-9 | AC-131: імітація результату (`action_simulate`, `optimizer.py`) **не** вилучена з модуля (TR AI-A08-15 пропонує перенести в `td_mebli_demo`): кнопка лишилась лише в режимі розробника | перенесення ламає демо й тести симулятора; зробити разом із підлаштуванням демо |
| G2-10 | AC-045: «Замінити» видаляє деталі специфікації від імені системи (технолог не має `unlink` на деталі за `ir.model.access`) | права `td.mebli.part` за `tr/security.md` (технолог RWCD) не змінено — окремий крок прав |

## Хвости для інших груп / сесії

- **G1 (AC-119):** поле `mrp.bom.td_cut_version` готове (0 — не відправлено); повідомлення блоку — `td.mebli.part._td_check_not_sent(boms)` (піднімає UserError AC-052).
- **G1 (AC-011/012):** `groups="td_mebli_base.group_feature_configurator"` на полях розмірів рядка продажу.
- **G3 (AC-121, 12-та картка):** журнал браку — `td.mebli.quality.check` з `kind='scrap'`, `result='fail'`, `note` (причина), `company_id`, `repeat_production_id`; невдалий крок якості — `kind='check'`, `result='fail'`. Ключ причини зсуву в дашборді: `'distributor'` замість `'cutting'`.
- **Демо (після G1–G4):** `scenario.py` крок 9 / `showcase.py` — завдання розкрою по декору; увімкнути FG `offcut`, `cutting_batch`, `kiosk`, `quality`, `label_scan` для коробки B; імпорт результату замість імітації.
- **A-13:** шаблон мапінгу `td.mebli.import.template` (name, header_signature = заголовки через `|` у нижньому регістрі, mapping_json `{поле: № колонки}`).

## Прогін

Чиста база `test-mebli-a11g2-r5` (без демо), `-i td_mebli_mrp,td_mebli_cutting,td_mebli_shop,td_mebli_purchase`, `--test-tags /td_mebli_mrp,/td_mebli_cutting,/td_mebli_shop,/td_mebli_purchase`, `--http-port=8172`:

**0 failed, 0 error(s) of 89 tests.** td_mebli_cutting 37, td_mebli_mrp 48, td_mebli_purchase 12, td_mebli_shop 28.

Переклад: усі нові рядки інтерфейсу й помилок перекладено в `i18n/uk.po` кожного модуля (експорт `i18n export -l uk` → 0 неперекладених у чотирьох модулях); `.pot` оновлено/додано (`td_mebli_shop.pot`, `td_mebli_purchase.pot` — нові). Один тест змінено в чужій логіці лише в межах G2-модуля: `td_mebli_cutting/tests/test_distributor.py` (причина зсуву `cutting`→`distributor`, G2-6). `td_mebli_shop/tests/test_shop.py` — оновлено текст AC-072 і ввімкнено registry test mode для лічильника PIN.
Не прогнано: тести інших груп (G1/G3/G4) і демо — поза test-tags цього прогону.
