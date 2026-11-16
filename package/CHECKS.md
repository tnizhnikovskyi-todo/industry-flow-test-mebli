# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 10, цикл 3, 2026-11-16)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка`. Причина — зауваження власника на гейті A-17 («Повернути»), рішення власника 2026-11-16 (зауваження A-17), `flow/decisions.md` рядок 58 (вносить головна сесія): A-11-fix7 (№6–9, 11, 15, 16 — AC-135…AC-140, D-26…D-30, D-34, D-35), A-12-8 (проєкт «Монтажі» зі стадіями), A-13-7 (`td/16` з усіма коефіцієнтами, D-25). Історія спроби 9 — у git (`09fc902`).

## Ревізія package/ (commit SHA)
`SHA: 2f527e891d9d25aa1280bde92a777df0b0c7b082`

## Прогін C-03
`SHA прогону: 2f527e8` (цикл 3; цикл 2 — `8e53688`, той самий результат) · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). Окремий каталог доставки `/home/user/odoo19/delivery-a17r` (лише `package/addons`), конфіги `odoo-tools-a17r{,-light,-B}.conf` (порти 8306–8308), профілі паралельно.

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 45 модулів) | test-mebli-a17r-a1410-A | 342 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 8 / 0 |
| light (`profiles/answers.alt-1.yaml`, 45) | test-mebli-a17r-a1410-light | 342 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 8 / 0 |
| B (`profiles/answers.alt-2.yaml`, 46) | test-mebli-a17r-a1410-B | 347 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 8 / 0 |

Формат клітинки — тестів / failed+error. Проти спроби 9: +14 тестів `td_mebli_*` (A-11-fix7: `td_mebli_sale` TestA17Sale 5, `td_mebli_measure` TestA17Measure 4, `td_mebli_install` TestA17InstallStages 5), +2 `td_home_menu` (№17: TestEeLookSwitch, тур `td_chatter_resize_tour`). Цикл 1 (`6f6f0de`, без №17) — те саме для `td_mebli_*`, `td_home_menu` 6 / 0; №17 додано в гілці A-14-10 (`8e53688`) і прогін повторено повністю (цикл 2); правка №43 з A-16-9 (`2f527e8`, у гілці A-16-9) — повний прогін цикл 3, ті самі числа.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 2f527e891d9d25aa1280bde92a777df0b0c7b082 | 2f527e8 success (локально, цикл 3) | APPROVE (замінники) | правки №42 (A-13) і №43 (A-11, з A-16-9) закриті в цьому ж контурі |
| ee | 2f527e891d9d25aa1280bde92a777df0b0c7b082 | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); `td_home_menu` при `web_enterprise` нічого не змінює (тест TestHomeMenuFlag) |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 17268db..8e53688) | APPROVE (замінник) | WARN: EE не перевірено | нові моделі/поля: `td.mebli.print.wizard` (transient, ACL base.group_user), `td.mebli.measure.event_id`, `calendar.event.td_measure_ids`, `project.project.td_install_project`, `sale.order.td_margin_warning`, `sale.order.line.td_dims_range/td_below_cost`; дані `project.task.type` (noupdate); перевизначення `crm.lead.action_schedule_meeting`, `sale.order.line._timesheet_create_task_prepare_values`, `sale.order.write` (commitment_date), `project.task.create/write`, `td.mebli.install.act.write` — усі через super(); `groups` з «!» — Odoo 19 `has_groups` |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | `sudo` з коментарями: створення замір-листа з нагодою (замірник не читає нагоду — AC-006; запис його, правило «свої заміри»), читання собівартості для причини від'ємної маржі (суми — лише MARGIN_GROUPS), стадія виїзду за датою/актом, список звітів (групи звіту перевіряються, як у ⚙ → «Друк»); `calendar.filters` — свої записи користувача; №17 — лише клієнтський код, `localStorage` у try/catch, без даних |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | `td_config.project_install` + `td_install_project`, `requires_module: td_mebli_install`; `apply.py plan` 7 профілів — без змін модулів, невідомих ключів 0 |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | ruff (E,F,W,B,I) змінених .py — нових знахідок 0, крім E501 1 рядка `help` (121 > 120, `install_project.py:16`, info); `.pot` — експорт `odoo-bin i18n export`, uk.po — нові тексти перекладено; test_d13/test_d16 PASS (A, light, B) |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-mebli-a17r-a1410-cv` (цикл 1; №17 конфіг і імпорт не зачіпає): модулі 45 + конфіг (8/4/14; повтор unchanged 26) + майстер-дані 25/25 (92 записи) + compare diff 0 + read-back 22 / 0 + smoke OK; «Монтажі»: прапорець і 5 стадій; SO → MO «Шафа-купе» трьох декорів — 3 деталі |

## Покриття ALLOCATION
- `package/addons/`: обсяг diff — `td_mebli_sale` 1.1.7, `td_mebli_measure` 1.1.5, `td_mebli_install` 1.1.9, `td_mebli_demo` 1.1.6, `td_home_menu` 1.0.3; нові AC-135…AC-141 — у ALLOCATION і AC-COVERAGE (done з тестами); D-34 (AC-014) — тест.
- `package/config/`, `package/master-data/`: змінено (A-12-8, A-13-7); track-convergence на налаштованій базі A.
- Покриття 100 % (CE) для AC збірки; виключені AC (BAS) — поза пакетом за рішенням власника.

## Правки
Цикли спроб 1–9: №1–41, D-18…D-21, UI-1, UI-2, T-1 закрито.
- **№43 (A-11, повернення A-16-9, закрито — цикл 3).** Колонка «Межі розміру, мм» обрізала довгий текст («ширина 800-2060 · висота …») — короткі позначки «Ш / В / Г» (`td_mebli_sale` 1.1.7); бренд навбару в режимі EE мав білий фон і переривав нижню лінію (`td_home_menu` 1.0.3). Коміт `2f527e8` у гілці A-16-9 (без force-push).
- **№42 (A-13, закрито в цьому контурі).** Приклад `td/16` «Полотно дверей-купе» (`facade_board`) у тест-імпорті деталі не давав — шаблон «Шафа-купе» купує готові фасади (`bought_facade`); замінено на «Задня стінка» (коміт A-13-7 `6f6f0de` у гілці A-14-10, без force-push), повторний імпорт 3/3, SO → MO — 3 деталі.

Info — не правки, без коду повернення:
- **N10-1.** Демо-стенд має два проєкти «Монтажі» (конфіг-пакет і `td_mebli_demo`), як і раніше; прапорець «Проєкт монтажів» — на обох.
- **N10-2.** №17 (вигляд у дусі EE, ширина чатера) — у збірці за умовою власника: тести зелені; тури A-16-9 і знімки 8 ролей — умова потрапляння на стенд показу (A-16-9, A-16b-7).

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — спроба 10 (цикл 3) на `2f527e8`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Зауваження власника A-17 (рішення власника 2026-11-16, `flow/decisions.md` рядок 58): №5–9, 11, 15, 16 і доробка №17 — код, конфіг, шаблони з тестами; №12–14 — посібники (A-16b-7); №1–4, №10 — беклог 1.1.
- C-03 — success: локальний прогін, цикл 3 (A 383, light 383, B 388 тестів; 0 failed).
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
