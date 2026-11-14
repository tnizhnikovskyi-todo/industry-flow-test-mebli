# Лог установки конфіг-пакета

- Редакції: both (з `docs/industries/mebli/OWNER-INTAKE.md`); нижче — `## Спроба 4 (повернення з A-14 спроби 2: `package/CHECKS.md` №33, №34)

- База: `test-mebli-a114-cfga` (чиста, uk_UA, Odoo 19.0 CE @ `40e9be2b`), профіль A — 43 модулі `manifest.yaml` (137 installed, установка rc=0, ERROR 0), модулі — робоче дерево `package/addons` (A-11 спроба 4: `td_mebli_mrp` 19.0.1.1.2, `td_mebli_install` 19.0.1.1.2, `td_mebli_migration` 19.0.1.1.4). Не odoo-mcp — `odoo-bin shell`. Після роботи базу видалено.
- Прохід 1 (VP-05 = `true`): created 8, updated 4, unchanged 14, manual 1, skipped 2, errors 0. Прохід 2: unchanged 26, created/updated 0 (ідемпотентно). Read-back 23/23 PASS (VP-05: `active` True, `ir.default` 1 = `td_mebli_sale.payment_term_td_furniture`, нове SO — «Меблі на замовлення»).
- №34 (`td_config.default_payment_term` без `applies_if`, `json_value` = `{{VP-05:payment_default}}`): повтор на тій самій базі з VP-05 = `false` — прохід f1: updated 2 (`payment_term_furniture_active` → `active` False, `default_payment_term` → `json_value` `false`), прохід f2: unchanged 24, updated 0; read-back 23/23 PASS (VP-05: `active` False, `ir.default` 1 з `false`, default покупця — порожньо). Новий покупець і нове SO — **без умови оплати** (не архівна). Назад VP-05 = `true` — updated 2, default знову умова модуля. Критерій read-back VP-05 = `false`: «default покупця порожній, усі `ir.default` поля = `false`» (раніше — «`ir.default` = 0»; записи установка не видаляє — `apply-semantics.md`).
- №33: «Ручні кроки» CONFIG.md і цей лог — `step_td_17` = послідовність **24** з 28 (`td_mebli_migration/data/td_mebli_migration_step_data.xml`; узгоджено з `master-data/README.md`).
- Після конфігу — майстер-дані A-13 спроби 4, 28 кроків, помилок 0; «Шафа-купе» SO → MO (білий / дуб / графіт) — плита й кромка лише декору, кількість = з деталей (`master-data/README.md` «Тест-імпорт»).
- Рядки нижче (спроба 3) про `td_config.default_payment_term` «skipped(applies_if)» для light — історія: зі спроби 4 пункт застосовується завжди (light: `json_value` `false`).

## Редакція ce` (перевірено, профілі A і light) і `## Редакція ee` (не перевірено: EE недоступна)
- Бази (ce), спроба 3: `test-mebli-r3cfg-A`, `test-mebli-r3cfg-light` — локальні чисті тестові бази пакета (`odoo-bin -i` у нову базу з `--load-language=uk_UA`), Odoo 19.0 CE @ `40e9be2b`, редакція ce (`web_enterprise` у списку модулів відсутній); допоміжна `test-mebli-r3cfg-std` (лише 26 стандартних модулів, для A-13); після кроку видалені (`dropdb`), сервери зупинені. Профіль B у спробі 3 не перепрогнано (правки №23, №26, config-review 1 B не змінюють, крім пункту умов оплати — той самий, що в A); B спроби 2 — read-back PASS
- SHA гілки: `4e96a56` (база кроку, `flow/A-12-2-test`; модулі A-11 спроби 3 — знімок `git archive` `package/addons` цього SHA в `--addons-path`, бо робоче дерево модулів паралельно править інша сесія)   Версія скіла: config-as-code (версія 0.3.1)   Режим: fix (спроба 3, повернення з A-14)
- Спосіб: **не odoo-mcp** (у тесті заборонено, `odoo_connections: []`) — локальний `odoo-bin` (база, модулі: один виклик `-i` зі списком профілю — Odoo ставить у порядку залежностей, порядок `manifest.yaml` перевірено окремо: порушень 0) і `odoo-bin shell` (preflight, дані, settings, 2-й прохід, read-back; скрипт застосування за `apply-semantics.md` — у scratchpad сесії, не в репо)
- Стан бази на старті (кожен профіль): чиста — `ir.model.data` з `module = td_config` = 0, `web_enterprise` немає, встановлено лише модулі профілю та їх залежності
- Відповіді: `package/templates/answers.example.yaml` + `default` схеми для `edition` (`ce`) і `contract_mode` (`unset`) = профіль A; **light — за SPEC §11.3**: A з `VP-01: light`, `VP-04: false`, `VP-05: false`, `VP-09: distributor` (спроба 2 перевіряла light з VP-05 = `true`, VP-09 = `both` — CHECKS №26)
- Секрети: не вносяться (лише змінні оточення); у файлах і лозі — немає

## Редакція ce

## Preflight (SPEC §11.3, `manifest.yaml` → `preflight`; до установки модулів)
| Відповіді | Результат | Порушення |
|---|---|---|
| A (`answers.example.yaml`) | OK | PF-08 ignore (VP-02/03/12 поза B — не пишуться) |
| light за §11.3 | OK | PF-06 ignore (VP-14, VP-15), PF-07 ignore (кіоск за PIN), PF-08 ignore |
| light із default схеми (лише `VP-01: light`) | **STOP** до установки | PF-03 error (VP-04 = true), PF-04 error (VP-05 = true), PF-05 error (VP-09 = both) — з поясненням із `message` |
| `edition: ee` + VP-01 = A | **STOP** до установки | PF-01 error (EE лише з VP-01 = B) |
| light за §11.3 + `VP-14: time`, `VP-15: stage` (не default) | OK, застосовано | `td_config.param_vp_14/15`, `settings_attendance_pin` — skipped(applies_if); у компанії `td_crew_split = equal`, `td_crew_base = final` (default модуля), `attendance_kiosk_use_pin = False` (A — `True`); read-back PASS |

## Покрокова установка (q29: у 0.1 замість «однієї команди»)
| № | Крок | Виклик (інструмент, без секретів) | Результат |
|---|---|---|---|
| 1 | preflight за `answers.yaml` | правила `manifest.yaml` `preflight` (вирази над відповідями); `error` → стоп | A, light: OK |
| 2 | модулі профілю (`when` за відповідями) | A — 43, light — 42 (без `td_mebli_bas`: `when: VP-04 == true and VP-01 != 'light'`) | список = список установки |
| 3 | чиста база + мова uk_UA (AC-N.01) + 26 стандартних модулів CE + `td_mebli_*` профілю (порядок `manifest.yaml`) | `odoo-bin -d test-mebli-r3cfg-<профіль> -i <список профілю> --load-language=uk_UA --no-http --stop-after-init` | ok: A — 17 `td_*`, 137 installed, 88 с; light — 16 `td_*`, 136, 87 с; ERROR у лозі 0 |
| 4 | перевірка «чиста» | `odoo-bin shell`: `ir.model.data` `module=td_config` = 0, `web_enterprise` відсутній | ok (A, light) |
| 5 | `data/15_accounting.yaml` (3 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 6 | `data/20_sale_project.yaml` (4 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 7 | `data/30_mrp_stock.yaml` (5 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 8 | `data/40_calendar_mail.yaml` (2 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 9 | `data/60_td_params.yaml` (13 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 10 | `data/70_feature_groups.yaml` (1 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 11 | `data/80_settings.yaml` (5 пункт.) | `odoo-bin shell`, MODE=apply | A / light: ok, errors 0 |
| 12 | 2-й прохід-порівняння за xml-id і полями (без записів) | `odoo-bin shell`, MODE=compare | розбіжностей 0 (A, light) |
| 13 | повторне застосування (ідемпотентність) | `odoo-bin shell`, MODE=apply | created=0 updated=0 (A, light) |
| 14 | read-back VP | `odoo-bin shell` (`res.company`, `res.config.settings` створений запис + `implied_ids` `base.group_user`, `ir.model.data` → запис, `ir.default`, `ir.module.module`) | 20/20 VP PASS у кожному профілі + AC-030, AC-004, settings |
| 15 | після імпорту майстер-даних A-13 (28 / 25 кроків) — порівняння ще раз | `odoo-bin shell`, MODE=compare | розбіжностей 0 (A, light) |
| 16 | зупинка й прибирання | процеси `odoo-bin` завершені (`--stop-after-init`, shell), `dropdb` баз `test-mebli-r3cfg-*` | ok |

## Прогін 1 (чиста база)
- A: created=8 updated=4 unchanged=14 manual=1 errors=0   (skipped за applies_if=2; settings — один `execute()`)
- light: created=7 updated=7 unchanged=7 manual=1 errors=0   (skipped за applies_if=8; settings — один `execute()`)

## Прохід 2 (порівняння за xml-id, без записів)
- A: розбіжностей=0 відсутніх=0 unchanged=26 manual=1 (skipped=2). Повторне застосування: created=0 updated=0 errors=0.
- light: розбіжностей=0 відсутніх=0 unchanged=21 manual=1 (skipped=8). Повторне застосування: created=0 updated=0 errors=0.

## Read-back VP
| VP | Очікувано A → у базі | light → у базі | Статус |
|---|---|---|---|
| VP-01 | A → A | light → light | PASS |
| VP-02 | [] → [] (applies_if: не застосовується → default) | [] → [] (applies_if: не застосовується → default) | PASS |
| VP-03 | uninstalled → uninstalled (applies_if: не застосовується → default) | uninstalled → uninstalled (applies_if: не застосовується → default) | PASS |
| VP-04 | installed → installed | uninstalled → uninstalled | PASS |
| VP-05 | True → active=True, ir.default=1, default покупця=td_mebli_sale.payment_term_td_furniture, td_milestone=order/install/act, умов з td_milestone=1 | False → active=False, ir.default=0, default покупця=None, td_milestone=order/install/act, умов з td_milestone=1 | PASS |
| VP-06 | warn → warn | warn → warn (applies_if: не застосовується → default) | PASS |
| VP-07 | 2 → 2 | 2 → 2 (applies_if: не застосовується → default) | PASS |
| VP-08 | False → False | False → False | PASS |
| VP-09 | both → both | distributor → distributor | PASS |
| VP-10 | 5 → 5 | 5 → 5 | PASS |
| VP-11 | 5 → 5.0 | 5 → 5.0 | PASS |
| VP-12 | 300 → 300 (applies_if: не застосовується → default) | 300 → 300 (applies_if: не застосовується → default) | PASS |
| VP-13 | 14 → 14 | 14 → 14 | PASS |
| VP-14 | equal → equal | equal → equal (applies_if: не застосовується → default) | PASS |
| VP-15 | final → final | final → final (applies_if: не застосовується → default) | PASS |
| VP-16 | True → True | True → True | PASS |
| VP-17 | "warning" → "warning" | "warning" → "warning" | PASS |
| VP-18 | account.{company_id}_sale_tax_template_vat20_psbo → account.1_sale_tax_template_vat20_psbo | account.{company_id}_sale_tax_template_vat20_psbo → account.1_sale_tax_template_vat20_psbo | PASS |
| edition | absent → absent | absent → absent | PASS |
| contract_mode | False → False | False → False | PASS |
| AC-030 templates | 6 | 6 | PASS |
| AC-004 alarm | True | True | PASS |
| settings | group_stock_multi_locations=True; group_stock_adv_location=True; group_mrp_routings=True; portal_confirmation_sign=True; attendance_kiosk_use_pin=True; group_product_variant=False | group_stock_multi_locations=True; group_stock_adv_location=True; group_mrp_routings=True; portal_confirmation_sign=True; group_product_variant=False | PASS |

VP-02: A, light — галочок 0, груп `td_mebli_base.group_feature_*` в `implied_ids` `base.group_user` 0. VP-05: умова модуля `td_mebli_sale.payment_term_td_furniture` (A — активна і default умова покупців компанії через `ir.default` → `sale.order.payment_term_id`; light — архівна, `ir.default` немає); власного запису умов оплати конфіг не створює — в базі одна умова з `td_milestone`. VP-14/15 у light — default модуля (applies_if, PF-06). VP-03 / VP-04 / `edition` — за станом модуля (`absent` = модуля немає в списку CE-бази). AC-030 / AC-004 — наявність xml-id модулів (`td_mebli_notify` 6 шаблонів, `td_mebli_measure.alarm_mail_measure_1day`).

## Config-log (еквівалент для `config-review`; передається йому як config-log)
Читання стану — бази `test-mebli-r3cfg-A` / `-light` (локальний `odoo-bin shell`, замість `connection_id` odoo-mcp).
| Пункт CONFIG.md | xml-id | Фактичне значення A / light (прогін 1 → прохід 2) | Статус (PASS/FAIL/MANUAL) |
|---|---|---|---|
| data/15_accounting.yaml · AC-N.03 | `td_config.company_country_ua` | updated→unchanged / updated→unchanged | PASS |
| data/15_accounting.yaml · AC-N.03 | `td_config.chart_ua_psbo` | updated→unchanged / updated→unchanged | PASS |
| data/15_accounting.yaml · AC-N.03 | `td_config.company_default_taxes` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/20_sale_project.yaml · AC-019, AC-020 | `td_config.payment_term_furniture_active` | unchanged→unchanged / updated→unchanged | PASS |
| data/20_sale_project.yaml · AC-019 | `td_config.default_payment_term` | created→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/20_sale_project.yaml · AC-043, AC-095 | `td_config.project_install` | created→unchanged / created→unchanged | PASS |
| data/20_sale_project.yaml · AC-043, AC-044 | `td_config.product_install` | created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_power_outage` | created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_no_material` | created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_breakdown` | created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-116 | `td_config.default_bom_consumption` | created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-024 | `td_config.route_mto_active` | updated→unchanged / updated→unchanged | PASS |
| data/40_calendar_mail.yaml · AC-001, AC-004 | `td_config.event_type_measure` | created→unchanged / created→unchanged | PASS |
| data/40_calendar_mail.yaml · AC-030 | `td_config.mail_templates_customer` | manual→manual / manual→manual | MANUAL |
| data/60_td_params.yaml · AC-N.07, AC-089, AC-121 | `td_config.param_vp_01` | unchanged→unchanged / updated→unchanged | PASS |
| data/60_td_params.yaml · AC-020, AC-021 | `td_config.param_vp_06` | unchanged→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/60_td_params.yaml · AC-031 | `td_config.param_vp_07` | unchanged→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/60_td_params.yaml · AC-017, AC-018 | `td_config.param_vp_08` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-026, AC-027, AC-028… | `td_config.param_vp_09` | unchanged→unchanged / updated→unchanged | PASS |
| data/60_td_params.yaml · AC-067, AC-124 | `td_config.param_vp_10` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-085, AC-086 | `td_config.param_vp_11` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-059, AC-060 | `td_config.param_vp_12` | skipped(applies_if)→skipped(applies_if) / skipped(applies_if)→skipped(applies_if) | N/A у A, light (applies_if) |
| data/60_td_params.yaml · AC-110, AC-124 | `td_config.param_vp_13` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-104 | `td_config.param_vp_14` | unchanged→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/60_td_params.yaml · AC-103, AC-104 | `td_config.param_vp_15` | unchanged→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/60_td_params.yaml · AC-043 | `td_config.param_vp_16` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-033, AC-034, AC-101 | `td_config.param_contract_mode` | unchanged→unchanged / unchanged→unchanged | PASS |
| data/70_feature_groups.yaml · AC-N.07, AC-011, AC-012… | `td_config.feature_groups_box` | skipped(applies_if)→skipped(applies_if) / skipped(applies_if)→skipped(applies_if) | N/A у A, light (applies_if) |
| data/80_settings.yaml · AC-024 | `td_config.settings_stock_routes` | execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-070 | `td_config.settings_workorders` | execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-117 | `td_config.settings_portal_sign` | execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-077 | `td_config.settings_attendance_pin` | execute()→unchanged / skipped(applies_if)→skipped(applies_if) | PASS (light: N/A, applies_if) |
| data/80_settings.yaml · AC-011 | `td_config.settings_variants` | execute()→unchanged / execute()→unchanged | PASS |

## Ручні пункти
- AC-030 шаблони листів покупцю — модуль `td_mebli_notify` (6 шаблонів є, read-back PASS); тексти — B-04.
- AC-107 типові причини премій і штрафів (`td.mebli.accrual.reason`) — шаблон A-13 `td/17` + крок міграції `step_td_17` (послідовність 24 з 28; спроба 4, CHECKS №33); імпорт — B-04 / B-06.
- Вихідна пошта (SMTP, пароль) — B-04.
- Спроба 3: пункт «AC-019 розмітка `td_milestone`» закрито записом модуля `td_mebli_sale.payment_term_td_furniture` (CHECKS №22).

## Помилки й виправлення
- Помилок установки модулів, preflight A / light і даних — 0. Зупинки preflight (STOP) — лише в навмисних негативних перевірках (light із default схеми, `edition: ee` + A).
- Спроба 2 → 3: `td_config.payment_term_stages` прибрано з даних; на базах спроби 2 він лишився б зайвим записом — бази видалені, клієнтських баз з ним немає.
## Редакція ee` (не перевірено: EE недоступна)
- Бази (ce): `test-mebli-a12r2-A`, `test-mebli-a12r2-light`, `test-mebli-a12r2-B` — локальні чисті тестові бази пакета (копії `test-mebli-a12r2-tpl`: `base` + uk_UA), Odoo 19.0 CE @ `40e9be2b`, редакція ce (`web_enterprise` у списку модулів відсутній); після кроку видалені (`dropdb`)
- SHA гілки: `4e0fdda` (база кроку, `flow/A-12-2-test`; модулі A-11 — `package/addons` цієї гілки в `--addons-path`)   Версія скіла: config-as-code (версія 0.3.1)   Режим: fix (спроба 2, повтор після A-11)
- Спосіб: **не odoo-mcp** (у тесті заборонено, `odoo_connections: []`) — локальний `odoo-bin` (база, модулі: один виклик `-i` зі списком профілю — Odoo ставить у порядку залежностей, порядок `manifest.yaml` перевірено окремо: порушень 0) і `odoo-bin shell` (дані, settings, 2-й прохід, read-back; скрипт застосування за `apply-semantics.md` — у scratchpad сесії, не в репо)
- Стан бази на старті (кожен профіль): чиста — `ir.model.data` з `module = td_config` = 0, `web_enterprise` немає, встановлено лише модулі профілю та їх залежності
- Відповіді: `package/templates/answers.example.yaml` + `default` схеми для `edition` (`ce`) і `contract_mode` (`unset`) = профіль A; light = A з `VP-01: light`, `VP-04: false`; B = A з `VP-01: B`, `VP-03: multi_install_fop`, `VP-06: block`, `VP-08: true`, `VP-12: 450`, `VP-17: strict`, `contract_mode: contract` (тестові значення не за замовчуванням — щоб read-back бачив запис, а не default модуля)
- Секрети: не вносяться (лише змінні оточення); у файлах і лозі — немає

## Редакція ce

## Покрокова установка (q29: у 0.1 замість «однієї команди»)
| № | Крок | Виклик (інструмент, без секретів) | Результат |
|---|---|---|---|
| 1 | чиста база + мова uk_UA (AC-N.01) | `odoo-bin -d test-mebli-a12r2-tpl -i base --load-language=uk_UA --no-http --stop-after-init`; далі `createdb -T test-mebli-a12r2-tpl test-mebli-a12r2-<профіль>` | ok (17 с) |
| 2 | перевірка «чиста» | `odoo-bin shell`: `ir.model.data` `module=td_config` = 0, `web_enterprise` відсутній | ok (A, light, B) |
| 3 | 26 стандартних модулів CE + `td_mebli_*` профілю (порядок `manifest.yaml`: `base_setup` … `base_import`, `td_mebli_base` … `td_mebli_notify`) | `odoo-bin -d test-mebli-a12r2-<профіль> -i <список профілю> --no-http --stop-after-init` | ok: A — 17 `td_*`, 137 installed, 88 с; light — 16 `td_*` (без `td_mebli_bas`), 136, 86 с; B — 18 `td_*` (+ `td_mebli_multico`), 138, 87 с; помилок 0, попереджень `Access Rights Inconsistency` у видах — 2 (lint A-14) |
| 4 | мости EE (`td_mebli_shopfloor`, `_quality`, `_fsm`, `_planning`, `_helpdesk`, `_sign`) і 6 `std-ee` | не ставились — CE-база, EE недоступна | N/A (розділ ee) |
| 5 | `data/15_accounting.yaml` (3 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 6 | `data/20_sale_project.yaml` (3 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 7 | `data/30_mrp_stock.yaml` (5 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 8 | `data/40_calendar_mail.yaml` (2 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 9 | `data/60_td_params.yaml` (13 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 10 | `data/70_feature_groups.yaml` (1 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 11 | `data/80_settings.yaml` (5 пункт.) | `odoo-bin shell`, MODE=apply | A / light / B: ok, errors 0 |
| 12 | 2-й прохід-порівняння за xml-id і полями (без записів) | `odoo-bin shell`, MODE=compare | розбіжностей 0 (A, light, B) |
| 13 | повторне застосування (ідемпотентність) | `odoo-bin shell`, MODE=apply | created=0 updated=0 (A, light, B) |
| 14 | read-back VP | `odoo-bin shell` (`res.company`, `res.config.settings` створений запис + `implied_ids` `base.group_user`, `ir.model.data` → запис, `ir.module.module`) | 20/20 VP PASS у кожному профілі + AC-030, AC-004, settings |
| 15 | зупинка й прибирання | процеси `odoo-bin` завершені (`--stop-after-init`, shell), `dropdb` баз `test-mebli-a12r2-*` | ok |

## Прогін 1 (чиста база)
- A: created=8 updated=5 unchanged=12 manual=1 errors=0   (skipped за applies_if=2; settings — один `execute()`)
- light: created=8 updated=6 unchanged=11 manual=1 errors=0   (skipped за applies_if=2; settings — один `execute()`)
- B: created=8 updated=10 unchanged=8 manual=1 errors=0   (skipped за applies_if=0; settings — один `execute()`)

## Прохід 2 (порівняння за xml-id, без записів)
- A: розбіжностей=0 відсутніх=0 unchanged=25 manual=1 (skipped=2). Повторне застосування: created=0 updated=0 errors=0.
- light: розбіжностей=0 відсутніх=0 unchanged=25 manual=1 (skipped=2). Повторне застосування: created=0 updated=0 errors=0.
- B: розбіжностей=0 відсутніх=0 unchanged=26 manual=1 (skipped=0). Повторне застосування: created=0 updated=0 errors=0.

## Read-back VP
| VP | Очікувано A → у базі | light → у базі | B → у базі | Статус |
|---|---|---|---|---|
| VP-01 | A → A | light → light | B → B | PASS |
| VP-02 | [] → [] (applies_if: не застосовується → default) | [] → [] (applies_if: не застосовується → default) | 10 груп → 10 груп | PASS |
| VP-03 | uninstalled → uninstalled (applies_if: не застосовується → default) | uninstalled → uninstalled (applies_if: не застосовується → default) | installed → installed | PASS |
| VP-04 | installed → installed | uninstalled → uninstalled | installed → installed | PASS |
| VP-05 | True → True | True → True | True → True | PASS |
| VP-06 | warn → warn | warn → warn | block → block | PASS |
| VP-07 | 2 → 2 | 2 → 2 | 2 → 2 | PASS |
| VP-08 | False → False | False → False | True → True | PASS |
| VP-09 | both → both | both → both | both → both | PASS |
| VP-10 | 5 → 5 | 5 → 5 | 5 → 5 | PASS |
| VP-11 | 5 → 5.0 | 5 → 5.0 | 5 → 5.0 | PASS |
| VP-12 | 300 → 300 (applies_if: не застосовується → default) | 300 → 300 (applies_if: не застосовується → default) | 450 → 450 | PASS |
| VP-13 | 14 → 14 | 14 → 14 | 14 → 14 | PASS |
| VP-14 | equal → equal | equal → equal | equal → equal | PASS |
| VP-15 | final → final | final → final | final → final | PASS |
| VP-16 | True → True | True → True | True → True | PASS |
| VP-17 | "warning" → "warning" | "warning" → "warning" | "strict" → "strict" | PASS |
| VP-18 | account.{company_id}_sale_tax_template_vat20_psbo → account.1_sale_tax_template_vat20_psbo | account.{company_id}_sale_tax_template_vat20_psbo → account.1_sale_tax_template_vat20_psbo | account.{company_id}_sale_tax_template_vat20_psbo → account.1_sale_tax_template_vat20_psbo | PASS |
| edition | absent → absent | absent → absent | absent → absent | PASS |
| contract_mode | False → False | False → False | contract → contract | PASS |
| AC-030 templates | 6 | 6 | 6 | PASS |
| AC-004 alarm | True | True | True | PASS |
| settings | group_stock_multi_locations=True; group_stock_adv_location=True; group_mrp_routings=True; portal_confirmation_sign=True; attendance_kiosk_use_pin=True; group_product_variant=False | group_stock_multi_locations=True; group_stock_adv_location=True; group_mrp_routings=True; portal_confirmation_sign=True; attendance_kiosk_use_pin=True; group_product_variant=False | group_td_feature_configurator=True; group_td_feature_offcut=True; group_td_feature_cutting_batch=True; group_td_feature_kiosk=True; group_td_feature_quality=True; group_td_feature_label_scan=True; group_td_feature_change_sign=True; group_td_feature_nbu=True; group_td_feature_ai_mapping=False; group_td_feature_analog=True; group_td_feature_shop_board=True; group_stock_multi_locations=True; group_stock_adv_location=True; group_mrp_routings=True; portal_confirmation_sign=True; attendance_kiosk_use_pin=True; group_product_variant=True | PASS |

VP-02: A, light — галочок 0, груп `td_mebli_base.group_feature_*` в `implied_ids` `base.group_user` 0; B — 10 груп (усі з VP-02, `ai_mapping` не обрано → немає). VP-03 / VP-04 / `edition` — за станом модуля (`absent` = модуля немає в списку CE-бази). AC-030 / AC-004 — наявність xml-id модулів (`td_mebli_notify` 6 шаблонів, `td_mebli_measure.alarm_mail_measure_1day`).

## Config-log (еквівалент для `config-review`; передається йому як config-log)
Читання стану — бази `test-mebli-a12r2-A` / `-light` / `-B` (локальний `odoo-bin shell`, замість `connection_id` odoo-mcp).
| Пункт CONFIG.md | xml-id | Фактичне значення A / light / B (прогін 1 → прохід 2) | Статус (PASS/FAIL/MANUAL) |
|---|---|---|---|
| data/15_accounting.yaml · AC-N.03 | `td_config.company_country_ua` | updated→unchanged / updated→unchanged / updated→unchanged | PASS |
| data/15_accounting.yaml · AC-N.03 | `td_config.chart_ua_psbo` | updated→unchanged / updated→unchanged / updated→unchanged | PASS |
| data/15_accounting.yaml · AC-N.03 | `td_config.company_default_taxes` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/20_sale_project.yaml · AC-019 | `td_config.payment_term_stages` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/20_sale_project.yaml · AC-043, AC-095 | `td_config.project_install` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/20_sale_project.yaml · AC-043, AC-044 | `td_config.product_install` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_power_outage` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_no_material` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-070 | `td_config.loss_breakdown` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-116 | `td_config.default_bom_consumption` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/30_mrp_stock.yaml · AC-024 | `td_config.route_mto_active` | updated→unchanged / updated→unchanged / updated→unchanged | PASS |
| data/40_calendar_mail.yaml · AC-001, AC-004 | `td_config.event_type_measure` | created→unchanged / created→unchanged / created→unchanged | PASS |
| data/40_calendar_mail.yaml · AC-030 | `td_config.mail_templates_customer` | manual→manual / manual→manual / manual→manual | MANUAL |
| data/60_td_params.yaml · AC-N.07, AC-089, AC-121 | `td_config.param_vp_01` | unchanged→unchanged / updated→unchanged / updated→unchanged | PASS |
| data/60_td_params.yaml · AC-020, AC-021 | `td_config.param_vp_06` | unchanged→unchanged / unchanged→unchanged / updated→unchanged | N/A у A, light (applies_if) |
| data/60_td_params.yaml · AC-031 | `td_config.param_vp_07` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | N/A у A, light (applies_if) |
| data/60_td_params.yaml · AC-017, AC-018 | `td_config.param_vp_08` | unchanged→unchanged / unchanged→unchanged / updated→unchanged | PASS |
| data/60_td_params.yaml · AC-026, AC-027, AC-028… | `td_config.param_vp_09` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-067, AC-124 | `td_config.param_vp_10` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-085, AC-086 | `td_config.param_vp_11` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-059, AC-060 | `td_config.param_vp_12` | skipped(applies_if)→skipped(applies_if) / skipped(applies_if)→skipped(applies_if) / updated→unchanged | N/A у A, light (applies_if) |
| data/60_td_params.yaml · AC-110, AC-124 | `td_config.param_vp_13` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-104 | `td_config.param_vp_14` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-103, AC-104 | `td_config.param_vp_15` | unchanged→unchanged / unchanged→unchanged / unchanged→unchanged | PASS |
| data/60_td_params.yaml · AC-043 | `td_config.param_vp_16` | updated→unchanged / updated→unchanged / updated→unchanged | PASS |
| data/60_td_params.yaml · AC-033, AC-034, AC-101 | `td_config.param_contract_mode` | unchanged→unchanged / unchanged→unchanged / updated→unchanged | PASS |
| data/70_feature_groups.yaml · AC-N.07, AC-011, AC-012… | `td_config.feature_groups_box` | skipped(applies_if)→skipped(applies_if) / skipped(applies_if)→skipped(applies_if) / execute()→unchanged | N/A у A, light (applies_if) |
| data/80_settings.yaml · AC-024 | `td_config.settings_stock_routes` | execute()→unchanged / execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-070 | `td_config.settings_workorders` | execute()→unchanged / execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-117 | `td_config.settings_portal_sign` | execute()→unchanged / execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-077 | `td_config.settings_attendance_pin` | execute()→unchanged / execute()→unchanged / execute()→unchanged | PASS |
| data/80_settings.yaml · AC-011 | `td_config.settings_variants` | execute()→unchanged / execute()→unchanged / execute()→unchanged | PASS |

## Ручні пункти
- AC-030 шаблони листів покупцю — модуль `td_mebli_notify` (6 шаблонів є, read-back PASS); тексти — B-04.
- AC-019 розмітка етапів `td_milestone` рядків `td_config.payment_term_stages` — не в даних (CFG-td-isolation); B-04 / A-11 — відкрите питання.
- AC-107 типові причини премій і штрафів (`td.mebli.accrual.reason`) — не в даних (CFG-td-isolation); шаблон A-13 `td/17` — відкрите питання.
- Вихідна пошта (SMTP, пароль) — B-04.

## Помилки й виправлення
- Перший прохід-порівняння профілю A (база, згодом видалена й перестворена) показав хибну розбіжність `portal_confirmation_sign`, `attendance_kiosk_use_pin`: скрипт читав `default_get`, а ці поля `related` на компанію. Виправлено скрипт (read-back через створений запис `res.config.settings` = якір `related`, `apply-semantics.md`); профіль A прогнано заново на новій чистій базі — розбіжностей 0. Дані конфіг-пакета не змінювались.
- Помилок установки модулів і даних — 0.
## Редакція ee

не перевірено: EE недоступна (доступу до Odoo 19 Enterprise немає). Профіль `ee` = `ce` + 6 `std-ee` (`mrp_workorder`, `quality_control`, `industry_fsm`, `planning`, `helpdesk`, `sign`) + 6 мостів `td_mebli_*` (`auto_install: True`, є в `package/addons` @ `4e0fdda`); перевірено лише статично: `ee ⊇ ce`, порядок залежностей (порушень 0), `std-ee`/мости відсутні в `ce`. Маніфестів EE-модулів у CE-вихідниках немає — ліцензія залежностей мостів «не перевірена» (WARN); ліцензія самих мостів (LGPL-3 при залежності від EE) — `tests/open-questions.md`. Установку, дані й read-back на EE-базі виконати, коли буде доступ (C-00 / ВП-4).

## Спроба 5 (A-12-5, D-10, 2026-11-14) — редакція ce
- Конфіг-пакет без змін (D-10: виключення атрибутів — дані виробу, `CONFIG.md` «Зміни версії», спроба 5).
- База `test-mebli-a117t-demo` (профіль `package/demo/answers.yaml`, 43 модулі, через кроки `package/demo/up.sh` з копією для бази групи T): прохід 1 — created 8 / updated 6 / unchanged 13 / manual 1 / errors 0; прохід 2 (compare) — unchanged 27 / diff 0 / missing 0; read-back — 23 VP, 0 failed; після демо-шару read-back — OK. Повтор підйому з остаточним кодом A-11-7 — той самий результат (`tests/reports/A-12-5.md`).
- Профіль A (`profiles/answers.alt-5.yaml`, база `test-mebli-a117t-a5`, без демо): прохід, повтор і read-back — OK.
- `product.template.attribute.exclusion` після демо-шару — 2 (шафа-купе, кухонний модуль: «ЛДСП Антрацит» ✕ «ПВХ 0,4 мм»).
