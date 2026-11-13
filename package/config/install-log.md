# Лог установки конфіг-пакета

- Редакції: both (з `docs/industries/mebli/OWNER-INTAKE.md`); нижче — `## Редакція ce` (перевірено, профілі A / light / B) і `## Редакція ee` (не перевірено: EE недоступна)
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
