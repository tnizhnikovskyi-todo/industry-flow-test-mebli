# Лог установки конфіг-пакета

- Редакції: both (з `docs/industries/mebli/OWNER-INTAKE.md`); нижче — `## Редакція ce` (перевірено) і `## Редакція ee` (не перевірено: EE недоступна)
- База (ce): `test-mebli-a12cfg` — локальна чиста тестова база пакета, Odoo 19.0 CE @ `40e9be2b`, редакція ce (`web_enterprise` у списку модулів відсутній); після кроку видалена (`dropdb`)
- SHA гілки: `351d4a8` (база кроку, `flow/A-12-test`)   Версія скіла: config-as-code (версія 0.3.1)   Режим: build
- Спосіб: **не odoo-mcp** (у тесті заборонено, `odoo_connections: []`) — локальний `odoo-bin` (база, модулі) і `odoo-bin shell` (дані, settings, 2-й прохід, read-back; команди зі stdin, семантика `apply-semantics.md`, upsert за xml-id `td_config.*`, `unlink` не викликався); `addons_path` = Odoo CE `addons` + `odoo/addons` + `package/addons` гілки кроку (через `--addons-path`, `odoo.conf` не змінено); HTTP не запускався (`--no-http`). install-one-command: N/A (скриптів немає)
- Стан бази на старті: чиста (`ir.model.data` з `module = td_config` — 0; встановлено 14 модулів `base`-набору після створення)
- Відповіді: `package/templates/answers.example.yaml` (профіль A); `edition`, `contract_mode` у прикладі відсутні — взято `default` схеми (`ce`, `unset`)
- Секрети: не вносяться (лише змінні оточення); у файлах і лозі — немає

## Редакція ce

## Покрокова установка (q29: у 0.1 замість «однієї команди»)
| № | Крок | Виклик (інструмент, без секретів) | Результат |
|---|---|---|---|
| 1 | чиста база + мова uk_UA (AC-N.01) | `odoo-bin -d test-mebli-a12cfg -i base --load-language=uk_UA --no-http --stop-after-init` | ok (9 с) |
| 2 | перевірка «чиста» | `odoo-bin shell`: `ir.model.data` `module=td_config` = 0 | ok |
| 3 | 26 стандартних модулів CE за порядком `manifest.yaml` (`base_setup` … `base_import`) | `odoo-bin -i base_setup,mail,calendar,portal,hr,crm,stock,mrp,project,account,sale_crm,sale_margin,sale_stock,sale_mrp,sale_project,purchase,purchase_stock,sale_purchase_stock,purchase_mrp,mrp_account,repair,l10n_ua,hr_attendance,hr_hourly_cost,maintenance,base_import --stop-after-init` | ok, 26/26 `installed`, ERROR/Traceback 0 |
| 4 | модулі `td_mebli_*` профілю A за порядком `manifest.yaml` | `odoo-bin -i td_mebli_base,td_mebli_mrp,…,td_mebli_notify --stop-after-init` (список оновлено автоматично) | **частково**: 11/17 `installed` (`_mrp`, `_sale`, `_measure`, `_cutting`, `_purchase`, `_ua`, `_shop`, `_install`, `_claim`, `_cost`, `_dashboard`); `invalid module names, ignored: td_mebli_base, td_mebli_attendance, td_mebli_maint, td_mebli_migration, td_mebli_notify, td_mebli_bas` — модулів немає в `package/addons` (дефект для A-11) |
| 5 | `td_mebli_multico` | не ставиться в профілі A (VP-03 застосовується лише при VP-01 = `B`) | N/A |
| 6 | `data/15_accounting.yaml` (країна UA, план `ua_psbo`, ПДВ 20 % за VP-18) | `odoo-bin shell`, MODE=apply | ok |
| 7 | `data/20_sale_project.yaml` (умови оплати етапами, проєкт «Монтажі», послуга «Монтаж») | те саме | ok |
| 8 | `data/30_mrp_stock.yaml` (3 причини втрат, `ir.default` споживання, маршрут MTO) | те саме | ok |
| 9 | `data/40_calendar_mail.yaml` (тип «Замір», нагадування листом за 1 день; шаблони листів — manual) | те саме | ok, 1 manual |
| 10 | `data/60_td_params.yaml` (VP треку «код», `edition`, `contract_mode`) | те саме | ok; VP-12 — N/A (applies_if VP-01 = B) |
| 11 | `data/70_feature_groups.yaml` (VP-02) | те саме | N/A (applies_if VP-01 = B); у профілі B — BLOCKED, доки немає `td_mebli_base` |
| 12 | `data/80_settings.yaml` (`res.config.settings` → `execute()`) | те саме | ok, 3 `execute()` |
| 13 | 2-й прохід-порівняння за xml-id (без записів) | `odoo-bin shell`, MODE=compare | розбіжностей 0 |
| 14 | повторне застосування (ідемпотентність) | `odoo-bin shell`, MODE=apply | created=0 updated=0 |
| 15 | read-back VP | `odoo-bin shell` (`ir.config_parameter`, `ir.model.data` → запис, `res.company`, `default_get`, `ir.module.module`) | 18 PASS, 1 FAIL (VP-04), 1 N/A (VP-02) |
| 16 | зупинка й прибирання | процеси `odoo-bin` завершені (`--stop-after-init`), `dropdb test-mebli-a12cfg` | ok |

## Прогін 1 (чиста база)
created=21 updated=6 unchanged=4 manual=1 errors=0   (skipped за applies_if=2, blocked=0)   тривалість: модулі 66 с, дані 4 с
## Прохід 2 (порівняння за xml-id, без записів)
розбіжностей=0 відсутніх=0 unchanged=31 manual=1 (skipped=2). Повторне застосування: created=0 updated=0 unchanged=31.
## Read-back VP
| VP | Очікувано (answers.example.yaml → transform) | У базі | Статус |
|---|---|---|---|
| VP-01 | "A" → A | A | PASS |
| VP-02 | ["configurator", "offcut", "cutting_batch", "kiosk", "quality", "label_scan", "change_sign", "nbu", "analog", "shop_board"] → (не застосовується; профіль A) | — | N/A |
| VP-03 | "single" → (не застосовується) не installed | немає в списку | PASS |
| VP-04 | true → installed | немає в списку модулів | FAIL |
| VP-05 | true → True | True | PASS |
| VP-06 | "warn" → warn | warn | PASS |
| VP-07 | 2 → 2 | 2 | PASS |
| VP-08 | false → false | false | PASS |
| VP-09 | "both" → both | both | PASS |
| VP-10 | 5 → 5 | 5 | PASS |
| VP-11 | 5 → 5 | 5 | PASS |
| VP-12 | 300 → (не застосовується) | — | PASS |
| VP-13 | 14 → 14 | 14 | PASS |
| VP-14 | "equal" → equal | equal | PASS |
| VP-15 | "final" → final | final | PASS |
| VP-16 | true → true | true | PASS |
| VP-17 | "warning" → "warning" | "warning" | PASS |
| VP-18 | true → account.1_sale_tax_template_vat20_psbo | account.1_sale_tax_template_vat20_psbo | PASS |
| edition | "ce" → ce | ce | PASS |
| contract_mode | "unset" → (немає) | (немає) | PASS |
VP-04 FAIL: `td_mebli_bas` немає в `package/addons` гілки кроку (новий модуль A-11) — у списку модулів бази його немає. VP-02 N/A: профіль A (`applies_if: VP-01 = B`), групи `td_mebli_base.group_feature_*` відсутні.

Settings (не VP; `default_get` / поле компанії): `group_stock_multi_locations` = True, `group_stock_adv_location` = True, `group_mrp_routings` = True, `group_product_variant` = False (профіль A), `res.company.portal_confirmation_sign` = True, `res.company.attendance_kiosk_use_pin` = True — PASS.

## Config-log (еквівалент для `config-review`; передається йому як config-log)
Читання стану — база `test-mebli-a12cfg` (локальний `odoo-bin shell`, замість `connection_id` odoo-mcp).
| Пункт CONFIG.md | xml-id | Фактичне значення (прогін 1 → прохід 2) | Статус (PASS/FAIL/MANUAL) |
|---|---|---|---|
| 15_accounting.yaml · AC AC-N.03 | `td_config.company_country_ua` | updated → прохід 2: unchanged | PASS |
| 15_accounting.yaml · AC AC-N.03 | `td_config.chart_ua_psbo` | loaded → прохід 2: unchanged | PASS |
| 15_accounting.yaml · AC AC-N.03 | `td_config.company_default_taxes` | unchanged → прохід 2: unchanged | PASS |
| 20_sale_project.yaml · AC AC-019 | `td_config.payment_term_stages` | created → прохід 2: unchanged | PASS |
| 20_sale_project.yaml · AC AC-043, AC-095 | `td_config.project_install` | created → прохід 2: unchanged | PASS |
| 20_sale_project.yaml · AC AC-043, AC-044 | `td_config.product_install` | created → прохід 2: unchanged | PASS |
| 30_mrp_stock.yaml · AC AC-070 | `td_config.loss_power_outage` | created → прохід 2: unchanged | PASS |
| 30_mrp_stock.yaml · AC AC-070 | `td_config.loss_no_material` | created → прохід 2: unchanged | PASS |
| 30_mrp_stock.yaml · AC AC-070 | `td_config.loss_breakdown` | created → прохід 2: unchanged | PASS |
| 30_mrp_stock.yaml · AC AC-116 | `td_config.default_bom_consumption` | created → прохід 2: unchanged | PASS |
| 30_mrp_stock.yaml · AC AC-024 | `td_config.route_mto_active` | updated → прохід 2: unchanged | PASS |
| 40_calendar_mail.yaml · AC AC-001, AC-004 | `td_config.event_type_measure` | created → прохід 2: unchanged | PASS |
| 40_calendar_mail.yaml · AC AC-004 | `td_config.alarm_mail_1day` | created → прохід 2: unchanged | PASS |
| 40_calendar_mail.yaml · AC AC-030 | `td_config.mail_templates_customer` | MANUAL → прохід 2: MANUAL | MANUAL |
| 60_td_params.yaml · AC AC-N.07, AC-089, AC-121 | `td_config.param_vp_01` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-020, AC-021 | `td_config.param_vp_06` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-031 | `td_config.param_vp_07` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-017, AC-018 | `td_config.param_vp_08` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-026, AC-027, AC-028… | `td_config.param_vp_09` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-067, AC-124 | `td_config.param_vp_10` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-085, AC-086 | `td_config.param_vp_11` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-059, AC-060 | `td_config.param_vp_12` | SKIP → прохід 2: SKIP | N/A (applies_if) |
| 60_td_params.yaml · AC AC-110, AC-124 | `td_config.param_vp_13` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-104 | `td_config.param_vp_14` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-103, AC-104 | `td_config.param_vp_15` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-043 | `td_config.param_vp_16` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-113, AC-126, AC-127… | `td_config.param_edition` | set → прохід 2: unchanged | PASS |
| 60_td_params.yaml · AC AC-033, AC-034, AC-101 | `td_config.param_contract_mode` | unchanged → прохід 2: unchanged | PASS |
| 70_feature_groups.yaml · AC AC-N.07, AC-011, AC-012… | `td_config.feature_groups_box` | SKIP → прохід 2: SKIP | N/A (applies_if) |
| 80_settings.yaml · AC AC-024 | `td_config.settings_stock_routes` | executed → прохід 2: unchanged | PASS |
| 80_settings.yaml · AC AC-070 | `td_config.settings_workorders` | executed → прохід 2: unchanged | PASS |
| 80_settings.yaml · AC AC-117 | `td_config.settings_portal_sign` | unchanged → прохід 2: unchanged | PASS |
| 80_settings.yaml · AC AC-077 | `td_config.settings_attendance_pin` | executed → прохід 2: unchanged | PASS |
| 80_settings.yaml · AC AC-011 | `td_config.settings_variants` | unchanged → прохід 2: unchanged | PASS |
## Ручні пункти
- AC-030 шаблони листів покупцю — модуль `td_mebli_notify` (A-11).
- AC-004 нагадування за замовчуванням для зустрічі «Замір» — `td_mebli_measure` (A-11).
- AC-019 розмітка етапів `td_milestone` — `td_mebli_sale` (A-11) / B-04.
- Вихідна пошта (SMTP, пароль) — B-04.

## Помилки й виправлення
- Крок 4: `WARNING odoo.modules.loading: invalid module names, ignored: td_mebli_base, td_mebli_attendance, td_mebli_maint, td_mebli_migration, td_mebli_notify, td_mebli_bas` — не виправляється даними (дефект для A-11).
- Пробний прогін до основного (та сама назва бази, видалена й створена знову): `account` на компанії без країни ставить план `generic_coa`; виправлено пунктами `td_config.company_country_ua` + `td_config.chart_ua_psbo` (`try_loading('ua_psbo')`), ERROR/Traceback — 0.

## Редакція ee

не перевірено: EE недоступна (доступу до Odoo 19 Enterprise немає; модулі `mrp_workorder`, `quality_control`, `industry_fsm`, `planning`, `helpdesk`, `sign` у CE є лише заглушками `ir_module_module.xml`; мостів `td_mebli_*` EE немає в `package/addons`). Статус — WARN, SKIP.
