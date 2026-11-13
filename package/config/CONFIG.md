# CONFIG — конфіг-пакет пакета mebli (A-12)

Скіл: `flow-package-build:config-as-code (версія 0.3.1)`, режим `build`, спроба 1. Входи: `package/ALLOCATION.md`, `package/SPEC.md` (§4, §11), `package/tr/00-architecture.md`, `package/templates/answers.yaml` і `answers.example.yaml` @ `351d4a8`. Формат — `config-as-code/references/config-package-format.md` (`format: 2`), редакції — `flow-package-build/references/editions-and-bridges.md`.

Зміст по AC складено напряму з SPEC/ALLOCATION: скіла `odoo19-mvp-build:config-spec` у сесії немає (див. «Відкриті питання»). Пункт без AC з ALLOCATION сюди не потрапляє. Кожне поле й запис звірено з вихідниками Odoo 19.0 CE @ `40e9be2b` і з чистою тестовою базою (`fields_get`, `ir.model.data`).

## Обсяг (з ALLOCATION)

| Набір | Склад |
|---|---|
| `AC_cfg` (трек стандарт / конфіг, крок A-12) | AC-001, AC-004, AC-011, AC-019, AC-024, AC-030, AC-043, AC-044, AC-070, AC-077, AC-082, AC-084, AC-095, AC-116, AC-117; NFR AC-N.01, AC-N.03, AC-N.07 |
| `M_std` | 26 стандартних модулів CE профілю A (таблиця нижче) |
| `M_ready` («готове») | 0 — рядків «готове» в ALLOCATION немає (REUSE-01…06), вендорингу немає |
| VP | VP-01…VP-18 + службові `edition`, `contract_mode` (20 ключів схеми) |

## Пункти конфігурації по AC

| AC | Що налаштовується | Пункт даних (`data/`) | Вид |
|---|---|---|---|
| AC-001 | CRM + календар (стандарт), тип зустрічі «Замір» | `40_calendar_mail.yaml`: `td_config.event_type_measure` | record |
| AC-004 | нагадування листом за 1 день | `40_calendar_mail.yaml`: `td_config.alarm_mail_1day` (шаблон `calendar.calendar_template_meeting_reminder`) | record |
| AC-011 | варіанти товару (конфігуратор коробки B) | `80_settings.yaml`: `td_config.settings_variants` (`group_product_variant` = VP-01 `B` і `configurator` у VP-02) | settings |
| AC-019 | умови оплати етапами 50/40/10 | `20_sale_project.yaml`: `td_config.payment_term_stages` (`active` = VP-05) | record |
| AC-024 | MTO + «Купити», багатокрокові маршрути | `30_mrp_stock.yaml`: `td_config.route_mto_active` (`stock.route_warehouse0_mto.active`); `80_settings.yaml`: `td_config.settings_stock_routes` | record, settings |
| AC-030 | шаблони листів покупцю | `40_calendar_mail.yaml`: `td_config.mail_templates_customer` — **manual** (шаблони в `td_mebli_notify`, A-11) | mail_template |
| AC-043, AC-044 | проєкт «Монтажі», послуга «Монтаж» зі створенням задачі | `20_sale_project.yaml`: `td_config.project_install`, `td_config.product_install` (`service_tracking: task_global_project`) | record |
| AC-070 | причини втрат «Відключення світла», «Немає матеріалу», «Поломка»; робочі завдання | `30_mrp_stock.yaml`: `td_config.loss_*`; `80_settings.yaml`: `td_config.settings_workorders` | record, settings |
| AC-077 | кіоск відвідувань за PIN | `80_settings.yaml`: `td_config.settings_attendance_pin` | settings |
| AC-082, AC-084 | стандарт (резерв, аналіз закупівель) | лише модулі `stock`, `mrp`, `purchase` | — |
| AC-095 | графік бригад у проєкті «Монтажі» | `td_config.project_install` (календар задач — стандарт) | record |
| AC-116 | споживання специфікацій (VP-17) | `30_mrp_stock.yaml`: `td_config.default_bom_consumption` (`ir.default` поля `mrp.bom.consumption`) | record |
| AC-117 | онлайн-підпис пропозиції | `80_settings.yaml`: `td_config.settings_portal_sign` (`portal_confirmation_sign`) | settings |
| AC-N.01 | мова uk_UA | установка бази з `--load-language=uk_UA` (`manifest.yaml: install.language`); переклади `td_*` — A-11 | — |
| AC-N.03 | `l10n_ua`, план рахунків `ua_psbo`, ПДВ 20 % (VP-18) | `15_accounting.yaml`: `td_config.company_country_ua`, `td_config.chart_ua_psbo`, `td_config.company_default_taxes` | record, chart |
| AC-N.07 | профіль коробки (VP-01, VP-02) | `manifest.yaml` (`when:`), `60_td_params.yaml`: `td_config.param_vp_01`, `70_feature_groups.yaml`: `td_config.feature_groups_box` | td_param, group |

Значення VP: `{{VP-xx}}` — `transform` з `vp-map.yaml`; `{{VP-xx:<ім'я>}}` — `transform_<ім'я>` того самого пункту (коли одне VP дає два поля або значення залежить від кількох VP). `applies_if` — зі схеми: невиконана умова = пункт не застосовується.

## Модулі до установки

Порядок — установки (топологічний за `depends`, перевірено за `__manifest__.py`: порушень 0). Профілі коробок: light = A без `td_mebli_bas` (VP-04 = `false`, AI-A10-05); B = A + `td_mebli_multico` (VP-03 = `multi_install_fop`) + feature-групи VP-02; C = B + профіль `ee`. Повний перелік з `origin` — `manifest.yaml`.

| № | Технічна назва | Джерело | AC | Редакція |
|---|---|---|---|---|
| 1 | `base_setup` | стандарт | AC-N.07 | CE |
| 2 | `mail` | стандарт | AC-030 | CE |
| 3 | `calendar` | стандарт | AC-001, AC-004 | CE |
| 4 | `portal` | стандарт | AC-117 | CE |
| 5 | `hr` | стандарт | AC-077 | CE |
| 6 | `crm` | стандарт | AC-001 | CE |
| 7 | `stock` | стандарт | AC-024, AC-082 | CE |
| 8 | `mrp` | стандарт | AC-070, AC-082, AC-116 | CE |
| 9 | `project` | стандарт | AC-095 | CE |
| 10 | `account` | конфіг | AC-019, AC-N.03 | CE |
| 11 | `sale_crm` | стандарт | AC-001 | CE |
| 12 | `sale_margin` | стандарт (залежність `td_mebli_sale`) | AC-017 | CE |
| 13 | `sale_stock` | стандарт | AC-024 | CE |
| 14 | `sale_mrp` | стандарт | AC-082 | CE |
| 15 | `sale_project` | конфіг | AC-043, AC-044 | CE |
| 16 | `purchase` | стандарт | AC-084 | CE |
| 17 | `purchase_stock` | конфіг | AC-024 | CE |
| 18 | `sale_purchase_stock` | стандарт | AC-024 | CE |
| 19 | `purchase_mrp` | стандарт (залежність `td_mebli_sale`) | AC-082 | CE |
| 20 | `mrp_account` | стандарт (залежність `td_mebli_mrp`) | AC-116 | CE |
| 21 | `repair` | стандарт (залежність `td_mebli_claim`) | AC-080 | CE |
| 22 | `l10n_ua` | конфіг (VP-18) | AC-N.03 | CE |
| 23 | `hr_attendance` | стандарт | AC-077 | CE |
| 24 | `hr_hourly_cost` | стандарт (залежність `td_mebli_shop`) | AC-061 | CE |
| 25 | `maintenance` | стандарт (залежність `td_mebli_maint`) | AC-076 | CE |
| 26 | `base_import` | стандарт (залежність `td_mebli_migration`) | AC-089 | CE |
| 27–44 | `td_mebli_base`, `_mrp`, `_sale`, `_measure`, `_cutting`, `_purchase`, `_ua`, `_shop`, `_install`, `_claim`, `_cost`, `_maint`, `_attendance`, `_bas` (VP-04), `_migration`, `_multico` (B, VP-03), `_dashboard`, `_notify` | код (A-11), `origin: td` | див. `manifest.yaml` | CE |
| 45–50 | `mrp_workorder`, `quality_control`, `industry_fsm`, `planning`, `helpdesk`, `sign` | стандарт EE (`origin: std-ee`) | AC-126…AC-130 | EE |
| 51–56 | мости `td_mebli_shopfloor`, `_quality`, `_fsm`, `_planning`, `_helpdesk`, `_sign` (`auto_install`) | код (A-11) | AC-126…AC-130 | EE |

Модулів «готове» (вендорених) немає. Ліцензії залежностей ядра: AGPL — 0 (перевірено за маніфестами Odoo 19 CE і `package/addons`); модулі `td_*`, яких ще немає в `package/addons`, — «ліцензія не перевірена» (WARN).

## Параметри установки (VP-xx)

| VP | Ключ (якір) | Трек | Ціль | AC |
|---|---|---|---|---|
| VP-01 | `ir.config_parameter:[key=td_mebli.vp_01]:value` + `manifest when:` | конфіг | профіль модулів light / A / B; поле `res.company.td_box_profile` реалізує модуль td_* (A-11) | AC-N.07, AC-089, AC-121 |
| VP-02 | `res.groups:xml_id=base.group_user:implied_ids` (групи `td_mebli_base.group_feature_*`) | конфіг | feature-групи коробки B; групи створює A-11; лише при VP-01 = `B` | AC-011, AC-012, AC-037, … AC-121 (19 AC) |
| VP-03 | `ir.module.module:[name=td_mebli_multico]:state` | конфіг | `multi_install_fop` → модуль `td_mebli_multico`; юрособи — B-04; лише при VP-01 = `B` | AC-035, AC-036 |
| VP-04 | `ir.module.module:[name=td_mebli_bas]:state` | конфіг | `true` → модуль `td_mebli_bas` | AC-021, AC-039…AC-042, AC-078, AC-109 |
| VP-05 | `account.payment.term:xml_id=td_config.payment_term_stages:active` | конфіг | умови оплати етапами активні / архівні | AC-019, AC-020, AC-031, AC-042, AC-065 |
| VP-06 | `ir.config_parameter:[key=td_mebli.vp_06]:value` | код | реалізує модуль td_* (A-11): `res.company.td_payment_control`; лише при VP-05 = `true` | AC-020, AC-021 |
| VP-07 | `ir.config_parameter:[key=td_mebli.vp_07]:value` | код | реалізує модуль td_* (A-11): `td_pay_reminder_days`; лише при VP-05 = `true` | AC-031 |
| VP-08 | `ir.config_parameter:[key=td_mebli.vp_08]:value` | код | реалізує модуль td_* (A-11): `td_margin_to_salesman` | AC-017, AC-018 |
| VP-09 | `ir.config_parameter:[key=td_mebli.vp_09]:value` | код | реалізує модуль td_* (A-11): меню розкрою `td_mebli_cutting` | AC-026…AC-028, AC-053…AC-056, AC-131 |
| VP-10 | `ir.config_parameter:[key=td_mebli.vp_10]:value` | код | реалізує модуль td_* (A-11): `td_stuck_days` | AC-067, AC-124 |
| VP-11 | `ir.config_parameter:[key=td_mebli.vp_11]:value` | код | реалізує модуль td_* (A-11): `td_price_threshold_pct` | AC-085, AC-086 |
| VP-12 | `ir.config_parameter:[key=td_mebli.vp_12]:value` | код | реалізує модуль td_* (A-11): `td_min_offcut_mm`; лише при VP-01 = `B` | AC-059, AC-060 |
| VP-13 | `ir.config_parameter:[key=td_mebli.vp_13]:value` | код | реалізує модуль td_* (A-11): `td_claim_overdue_days` | AC-110, AC-124 |
| VP-14 | `ir.config_parameter:[key=td_mebli.vp_14]:value` | код | реалізує модуль td_* (A-11): `td_crew_split` | AC-104 |
| VP-15 | `ir.config_parameter:[key=td_mebli.vp_15]:value` | код | реалізує модуль td_* (A-11): `td_crew_base` | AC-103, AC-104 |
| VP-16 | `ir.config_parameter:[key=td_mebli.vp_16]:value` | код | реалізує модуль td_* (A-11): `td_install_in_price` | AC-043 |
| VP-17 | `ir.default:xml_id=td_config.default_bom_consumption:json_value` | конфіг | споживання нових специфікацій `flexible` / `warning` / `strict` | AC-116 |
| VP-18 | `res.company:xml_id=base.main_company:account_sale_tax_id` | конфіг | `true` → ПДВ 20 % `ua_psbo` за замовчуванням продажу й закупівлі; `false` → без податку за замовчуванням | AC-N.03 |
| edition | `ir.config_parameter:[key=td_mebli.edition]:value` + `manifest edition_profiles` | конфіг | профіль `ce` / `ee` | AC-113, AC-126…AC-130 |
| contract_mode | `ir.config_parameter:[key=td_mebli.contract_mode]:value` | код | реалізує модуль td_* (A-11): `res.company.td_contract_mode`; `unset` → параметра немає | AC-033, AC-034, AC-101 |

Ключ `td_mebli.<vp>` — контракт за замовчуванням `config-as-code` до рішення A-11 (WARN `td_param`); цільове поле компанії — `vp-map.yaml` `a11_target` (рішення AI-A12-01 нижче).

## Команда установки

Версія 0.1: команди немає — скриптів `tools/odoo/` немає (C-00 ще не скопіював еталони). Застосовано **не через odoo-mcp** (у тесті заборонено), а локальним Odoo 19.0 CE: `odoo-bin` для бази й модулів і `odoo-bin shell` (команди зі stdin, файлів у репо не створено) за семантикою `apply-semantics.md`. Покрокова інструкція (q29) — `install-log.md`, розділ «Покрокова установка». Вручну — за runbook (`config-runbook`). `install-one-command: N/A`.

## Ручні кроки

| Пункт CONFIG | Чому не дані (секрет / інтеграція / Studio / інше) | Хто виконує | Підтвердження |
|---|---|---|---|
| AC-030 шаблони листів покупцю | шаблони — `data/*.xml` модуля `td_mebli_notify` (A-11, хвиля 2), не конфіг-пакет | A-11 (модуль), Тімлід перевіряє в A-14 | установка `td_mebli_notify` + шаблони в базі |
| AC-004 зв'язок «тип зустрічі Замір → нагадування за 1 день» | у CE `calendar.event.type` має лише `name`, `color`; нагадування за замовчуванням для зустрічі заміру ставить код (`td_mebli_measure`) | A-11 | тур A-16 «запис на замір» |
| AC-019 розмітка етапів (`td_milestone`) рядків умов оплати | поле `td_*` — не в даних конфіг-пакета (CFG-td-isolation) | A-11 (`td_mebli_sale`: розмітка за порядком рядків) або B-04 | AC-019 на демо A-15 |
| Вихідна пошта для нагадувань | сервер SMTP з паролем — секрет | B-04 (база клієнта), пароль зі змінних оточення | тестовий лист |

Ручних пунктів: 4 (у даних `manual: true` — 1: `td_config.mail_templates_customer`).

## Зміни версії

Перший запуск (`build`), попереднього тега `package/vX.Y` немає.

## Відкриті питання

- Скілів `odoo19-mvp-build:config-spec`, `odoo19-mvp-build:config-review`, `boost:odoo19-lint`, `boost:source-check` у сесії немає: зміст CONFIG.md складено напряму з SPEC/ALLOCATION, `config-review` і `lint` — не виконано (звіт A-12).
- Модулі `td_mebli_base`, `td_mebli_maint`, `td_mebli_attendance`, `td_mebli_bas`, `td_mebli_migration`, `td_mebli_multico`, `td_mebli_notify` і мости EE відсутні в `package/addons` гілки кроку — установка профілю неповна (дефект для A-11).
- Ключі VP треку «код»: модулі зрізу читають власні ключі (`td_mebli_install.payment_control`, `td_mebli_sale.contract_mode` зі значеннями `work`/`sale`), а схема A-09 — `contract_mode: contract|sale|unset`; ТР (`tr/td_mebli_base.md`) переносить їх у поля компанії. A-11 обирає: читати `td_mebli.<vp>` або поле компанії (тоді A-12 змінює якір).
- AC-004: як прив'язати нагадування за 1 день до зустрічі «Замір» у CE (тип зустрічі не має нагадувань) — механізм A-11.
- AC-011: атрибути й виключення «Шафа-купе» — майстер-дані (A-13 / B-04), не конфіг.
- Профіль light (AI-A10-05): розрив залежностей `td_mebli_install` → `td_mebli_shop`, `td_mebli_dashboard` → усі A — рішення A-11 / Архітектора.
- Профіль `ee` не перевірено: доступу до Odoo 19 EE немає.
- План рахунків: `account` при установці на компанію без країни ставить `generic_coa`; пакет перемикає на `ua_psbo` (`try_loading`) на чистій базі без проводок. На базі з проводками перемикання неможливе — B-04 ставить країну UA до установки `account`.

## Рішення AI з ризиком (власник — вето; записи 28, 37, 48)

| ID | Рішення | Альтернатива | Ризик | Перевірка |
|---|---|---|---|---|
| AI-A12-01 | VP треку «код» пишуться в `ir.config_parameter` ключами `td_mebli.<vp>` (контракт скіла), цільове поле компанії — у `vp-map.yaml` `a11_target` | писати відразу в поля `res.company.td_*` (AI-A08-04) | полів ще немає (`td_mebli_base` відсутній); подвійне зберігання, якщо A-11 обере поле | A-11 рішення ключа; A-14 track-convergence |
| AI-A12-02 | План рахунків `ua_psbo` і країна UA — пункти даних (`kind: chart`, record компанії) після установки модулів | ставити країну до установки `account` (порушує порядок «модулі → дані») | на базі з проводками `try_loading` не перемкне план | B-04 runbook: країна до установки |
| AI-A12-03 | Послуга «Монтаж» і проєкт «Монтажі» — у конфіг-пакеті (ALLOCATION відносить AC-043 до A-12), без ціни | шаблон майстер-даних A-13 | дубль із шаблоном A-13 | A-13 README «Не дублювати конфіг» |
| AI-A12-04 | VP-03, VP-04 — `kind: module` (read-back за станом модуля); у `config-kinds-odoo19.md` такого виду немає | лише `manifest when:` без read-back | розширення формату без рішення Архітектора | observation, A-14 config-review |
| AI-A12-05 | VP-17 — `ir.default` поля `mrp.bom.consumption` (нові специфікації) | поле на кожній специфікації (A-11) | специфікації, створені кодом з явним `consumption`, ігнорують замовчування | A-11 (AI-A08-27), тур A-16 |
