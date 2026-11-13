# CONFIG — конфіг-пакет пакета mebli (A-12)

Скіл: `flow-package-build:config-as-code (версія 0.3.1)`, спроба 1 — режим `build` @ `351d4a8` (escalated: бракувало модулів A-11); **спроба 2 — режим `fix` @ `4e0fdda`** (повтор після A-11: модулі `td_mebli_*` є в `package/addons`, VP треку «код» — поля `res.company.td_*` модуля `td_mebli_base`, API G0 `package/addons/AC-COVERAGE.md`). Входи: `package/ALLOCATION.md`, `package/SPEC.md` (§4, §11), `package/tr/00-architecture.md`, `package/templates/answers.yaml` і `answers.example.yaml`, `package/addons/` @ `4e0fdda`. Формат — `config-as-code/references/config-package-format.md` (`format: 2`), редакції — `flow-package-build/references/editions-and-bridges.md`.

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
| AC-004 | нагадування листом за 1 день до заміру | запис модуля `td_mebli_measure.alarm_mail_measure_1day` (майстер запису ставить його на зустріч); тип зустрічі — `td_config.event_type_measure`; пункт спроби 1 `td_config.alarm_mail_1day` прибрано (дубль) | record (модуль) |
| AC-011 | варіанти товару (конфігуратор коробки B) | `80_settings.yaml`: `td_config.settings_variants` (`group_product_variant` = VP-01 `B` і `configurator` у VP-02) | settings |
| AC-019 | умови оплати етапами 50/40/10 | `20_sale_project.yaml`: `td_config.payment_term_stages` (`active` = VP-05) | record |
| AC-024 | MTO + «Купити», багатокрокові маршрути | `30_mrp_stock.yaml`: `td_config.route_mto_active` (`stock.route_warehouse0_mto.active`); `80_settings.yaml`: `td_config.settings_stock_routes` | record, settings |
| AC-030 | шаблони листів покупцю | `40_calendar_mail.yaml`: `td_config.mail_templates_customer` — **manual**: 6 шаблонів постачає `td_mebli_notify` (`data/mail_template_data.xml`), read-back перевіряє їх xml-id | mail_template |
| AC-043, AC-044 | проєкт «Монтажі», послуга «Монтаж» зі створенням задачі | `20_sale_project.yaml`: `td_config.project_install`, `td_config.product_install` (`service_tracking: task_global_project`) | record |
| AC-070 | причини втрат «Відключення світла», «Немає матеріалу», «Поломка»; робочі завдання | `30_mrp_stock.yaml`: `td_config.loss_*`; `80_settings.yaml`: `td_config.settings_workorders` | record, settings |
| AC-077 | кіоск відвідувань за PIN | `80_settings.yaml`: `td_config.settings_attendance_pin` | settings |
| AC-082, AC-084 | стандарт (резерв, аналіз закупівель) | лише модулі `stock`, `mrp`, `purchase` | — |
| AC-095 | графік бригад у проєкті «Монтажі» | `td_config.project_install` (календар задач — стандарт) | record |
| AC-116 | споживання специфікацій (VP-17) | `30_mrp_stock.yaml`: `td_config.default_bom_consumption` (`ir.default` поля `mrp.bom.consumption`) | record |
| AC-117 | онлайн-підпис пропозиції | `80_settings.yaml`: `td_config.settings_portal_sign` (`portal_confirmation_sign`) | settings |
| AC-N.01 | мова uk_UA | установка бази з `--load-language=uk_UA` (`manifest.yaml: install.language`); переклади `td_*` — A-11 | — |
| AC-N.03 | `l10n_ua`, план рахунків `ua_psbo`, ПДВ 20 % (VP-18) | `15_accounting.yaml`: `td_config.company_country_ua`, `td_config.chart_ua_psbo`, `td_config.company_default_taxes` | record, chart |
| AC-N.07 | профіль коробки (VP-01, VP-02) | `manifest.yaml` (`when:`), `60_td_params.yaml`: `td_config.param_vp_01` (`res.company.td_box_profile`), `70_feature_groups.yaml`: `td_config.feature_groups_box` (галочки `group_td_feature_*`) | td_param, settings |

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

Модулів «готове» (вендорених) немає. Ліцензії залежностей ядра: AGPL — 0 (перевірено за маніфестами Odoo 19 CE і `package/addons`); модулі `td_*` — LGPL-3 (маніфести `package/addons` @ `4e0fdda`); мости EE залежать від модулів EE, яких немає в CE-вихідниках — «ліцензія залежності не перевірена» (WARN), ліцензія самих мостів — відкрите питання (`tests/open-questions.md`).

## Параметри установки (VP-xx)

| VP | Ключ (якір) | Трек | Ціль | AC |
|---|---|---|---|---|
| VP-01 | `res.company:xml_id=base.main_company:td_box_profile` + `manifest when:` | конфіг | профіль модулів light / A / B + поле `res.company.td_box_profile` (td_mebli_base) | AC-N.07, AC-089, AC-121 |
| VP-02 | `res.config.settings` `group_td_feature_<значення>` → `td_mebli_base.group_feature_*` у `implied_ids` `base.group_user` | конфіг | feature-групи коробки B (галочки налаштувань td_mebli_base); лише при VP-01 = `B` | AC-011, AC-012, AC-037, … AC-121 (19 AC) |
| VP-03 | `ir.module.module:[name=td_mebli_multico]:state` | конфіг | `multi_install_fop` → модуль `td_mebli_multico`; юрособи — B-04; лише при VP-01 = `B` | AC-035, AC-036 |
| VP-04 | `ir.module.module:[name=td_mebli_bas]:state` | конфіг | `true` → модуль `td_mebli_bas` | AC-021, AC-039…AC-042, AC-078, AC-109 |
| VP-05 | `account.payment.term:xml_id=td_config.payment_term_stages:active` | конфіг | умови оплати етапами активні / архівні | AC-019, AC-020, AC-031, AC-042, AC-065 |
| VP-06 | `res.company:xml_id=base.main_company:td_payment_control` | код | реалізує модуль td_* (A-11): `res.company.td_payment_control`; лише при VP-05 = `true` | AC-020, AC-021 |
| VP-07 | `res.company:xml_id=base.main_company:td_pay_reminder_days` | код | реалізує модуль td_* (A-11): `td_pay_reminder_days`; лише при VP-05 = `true` | AC-031 |
| VP-08 | `res.company:xml_id=base.main_company:td_margin_to_salesman` | код | реалізує модуль td_* (A-11): `td_margin_to_salesman` | AC-017, AC-018 |
| VP-09 | `res.company:xml_id=base.main_company:td_cutting_mode` | код | реалізує модуль td_* (A-11): `td_cutting_mode` (`distributor` ховає меню власного розкрою) | AC-026…AC-028, AC-053…AC-056, AC-131 |
| VP-10 | `res.company:xml_id=base.main_company:td_stuck_days` | код | реалізує модуль td_* (A-11): `td_stuck_days` | AC-067, AC-124 |
| VP-11 | `res.company:xml_id=base.main_company:td_price_threshold_pct` | код | реалізує модуль td_* (A-11): `td_price_threshold_pct` | AC-085, AC-086 |
| VP-12 | `res.company:xml_id=base.main_company:td_min_offcut_mm` | код | реалізує модуль td_* (A-11): `td_min_offcut_mm`; лише при VP-01 = `B` | AC-059, AC-060 |
| VP-13 | `res.company:xml_id=base.main_company:td_claim_overdue_days` | код | реалізує модуль td_* (A-11): `td_claim_overdue_days` | AC-110, AC-124 |
| VP-14 | `res.company:xml_id=base.main_company:td_crew_split` | код | реалізує модуль td_* (A-11): `td_crew_split` | AC-104 |
| VP-15 | `res.company:xml_id=base.main_company:td_crew_base` | код | реалізує модуль td_* (A-11): `td_crew_base` | AC-103, AC-104 |
| VP-16 | `res.company:xml_id=base.main_company:td_install_in_price` | код | реалізує модуль td_* (A-11): `td_install_in_price` | AC-043 |
| VP-17 | `ir.default:xml_id=td_config.default_bom_consumption:json_value` | конфіг | споживання нових специфікацій `flexible` / `warning` / `strict` | AC-116 |
| VP-18 | `res.company:xml_id=base.main_company:account_sale_tax_id` | конфіг | `true` → ПДВ 20 % `ua_psbo` за замовчуванням продажу й закупівлі; `false` → без податку за замовчуванням | AC-N.03 |
| edition | `manifest edition_profiles`; read-back — `ir.module.module:[name=web_enterprise]:state` (`ce` = відсутній) | конфіг | профіль `ce` / `ee` | AC-113, AC-126…AC-130 |
| contract_mode | `res.company:xml_id=base.main_company:td_contract_mode` | код | реалізує модуль td_* (A-11): `res.company.td_contract_mode`; `unset` → поле порожнє | AC-033, AC-034, AC-101 |

Трек «код»: `kind: td_param` з якорем — поле `res.company.td_*` модуля `td_mebli_base` (AI-A08-04, рішення AI-A12-01 спроби 2); ключі `ir.config_parameter` `td_mebli.<vp>` спроби 1 більше не пишуться (`post_init_hook` `td_mebli_base` переносить їх у поля, якщо вони є в базі). Запис — у `base.main_company`; у базі з кількома юрособами (B-04, VP-03) — значення на кожну компанію.

## Команда установки

Версія 0.1: команди немає — скриптів `tools/odoo/` немає (C-00 ще не скопіював еталони). Застосовано **не через odoo-mcp** (у тесті заборонено), а локальним Odoo 19.0 CE: `odoo-bin` для бази й модулів і `odoo-bin shell` (скрипт застосування — у scratchpad сесії, не в репо) за семантикою `apply-semantics.md`. Покрокова інструкція (q29) — `install-log.md`, розділ «Покрокова установка». Вручну — за runbook (`config-runbook`). `install-one-command: N/A`.

## Ручні кроки

| Пункт CONFIG | Чому не дані (секрет / інтеграція / Studio / інше) | Хто виконує | Підтвердження |
|---|---|---|---|
| AC-030 шаблони листів покупцю | шаблони постачає модуль `td_mebli_notify` (`data/mail_template_data.xml`, 6 записів); конфіг-пакет їх не дублює | A-11 (модуль); тексти — B-04 | read-back: 6 xml-id `td_mebli_notify.mail_template_td_*` є (`install-log.md`) |
| AC-019 розмітка етапів (`td_milestone`: передоплата / перед монтажем / акт) рядків умов оплати `td_config.payment_term_stages` | поле `td_*` на стандартній моделі — не в даних конфіг-пакета (CFG-td-isolation), хоча `AC-COVERAGE.md` (AC-019) віддає розмітку «даним A-12» — розбіжність, `tests/open-questions.md` | B-04 (вручну на формі умов оплати) або A-11 (data XML модуля) — рішення Архітектора | AC-019 на демо A-15 |
| AC-107 типові причини премій і штрафів (`td.mebli.accrual.reason`) | модель `td.*` — не в конфіг-пакеті (CFG-td-isolation), хоча докстрінг моделі каже «типовий набір — дані конфіг-пакета»; шаблон — A-13 `td/17_td.mebli.accrual.reason.csv` | A-13 (шаблон) / B-04 (імпорт) | `tests/open-questions.md` |
| Вихідна пошта для нагадувань | сервер SMTP з паролем — секрет | B-04 (база клієнта), пароль зі змінних оточення | тестовий лист |

Ручних пунктів: 4 (у даних `manual: true` — 1: `td_config.mail_templates_customer`). Пункт спроби 1 «AC-004 зв'язок типу зустрічі з нагадуванням» закрито модулем `td_mebli_measure`.

## Зміни версії

Перший запуск (`build`), попереднього тега `package/vX.Y` немає. Спроба 2 (`fix`, після A-11 @ `4e0fdda`, правок A-14 немає — `CHECKS.md` відсутній):

| Що | Спроба 1 | Спроба 2 |
|---|---|---|
| VP треку «код» (VP-06…VP-16), VP-01, `contract_mode` | `ir.config_parameter` `td_mebli.<vp>` + `a11_target` | поля `res.company.td_*` (`td_mebli_base`), `a11_target` прибрано; VP-09 → `td_cutting_mode` |
| VP-02 | `implied_ids` `base.group_user` напряму (kind `group`) | галочки `res.config.settings` `group_td_feature_*` (API G0), kind `settings` |
| `edition` | `ir.config_parameter` `td_mebli.edition` (код не читає) | лише профіль `edition_profiles`; read-back — `web_enterprise` |
| `contract_mode = unset` | параметра немає | поле `td_contract_mode` порожнє |
| AC-004 | `td_config.alarm_mail_1day` | прибрано (дубль `td_mebli_measure.alarm_mail_measure_1day`) |
| Модулі | 7 `td_*` і 6 мостів відсутні | усі 18 `td_*` CE і 6 мостів є в `package/addons`; профілі A / light / B встановлено |

## Відкриті питання

- Скілів `odoo19-mvp-build:config-spec`, `odoo19-mvp-build:config-review`, `boost:odoo19-lint`, `boost:source-check` у сесії немає: зміст CONFIG.md складено напряму з SPEC/ALLOCATION, `config-review` і `lint` — не виконано (звіт A-12-2).
- AC-019 `td_milestone` і AC-107 причини нарахувань: A-11 віддає їх «даним конфіг-пакета», а `config-as-code` забороняє `td_*` у даних (CFG-td-isolation) — хто постачає (A-11 data XML / A-13 шаблон / B-04) — `tests/open-questions.md`.
- AC-011: атрибути й виключення «Шафа-купе» — майстер-дані (A-13 / B-04), не конфіг.
- Профіль light (AI-A10-05): розрив залежностей `td_mebli_install` → `td_mebli_shop`, `td_mebli_dashboard` → усі A — рішення A-11 / Архітектора; у спробі 2 light = A без `td_mebli_bas` (встановлено й перевірено).
- Профіль `ee` не перевірено: доступу до Odoo 19 EE немає; мости встановлювались лише статично (маніфести, порядок).
- План рахунків: `account` при установці на компанію без країни ставить `generic_coa`; пакет перемикає на `ua_psbo` (`try_loading`) на чистій базі без проводок. На базі з проводками перемикання неможливе — B-04 ставить країну UA до установки `account`.
- Кілька юрос (VP-03 `multi` / `multi_install_fop`): пункти `td_param` пишуться в `base.main_company`; інші компанії створює B-04 — значення VP для них (default модуля або ті самі відповіді) — B-04 runbook.

## Рішення AI з ризиком (власник — вето; записи 28, 37, 48)

| ID | Рішення | Альтернатива | Ризик | Перевірка |
|---|---|---|---|---|
| AI-A12-01 (спроба 2) | VP треку «код», VP-01, `contract_mode` — `kind: td_param` з якорем поле `res.company.td_*` (`td_mebli_base`), запис у `base.main_company`; ключі `ir.config_parameter` спроби 1 не пишуться | писати ключі `td_mebli.<vp>` і покладатися на `post_init_hook` | компанії, створені після конфігу (B-04, кілька юрос), отримують default модуля, а не відповідь анкети | read-back A / light / B; B-04 runbook |
| AI-A12-02 | План рахунків `ua_psbo` і країна UA — пункти даних (`kind: chart`, record компанії) після установки модулів | ставити країну до установки `account` (порушує порядок «модулі → дані») | на базі з проводками `try_loading` не перемкне план | B-04 runbook: країна до установки |
| AI-A12-03 | Послуга «Монтаж» і проєкт «Монтажі» — у конфіг-пакеті (ALLOCATION відносить AC-043 до A-12), без ціни | шаблон майстер-даних A-13 | дубль із шаблоном A-13 | A-13 README «Не дублювати конфіг» |
| AI-A12-04 | VP-03, VP-04, `edition` — `kind: module` (read-back за станом модуля); у `config-kinds-odoo19.md` такого виду немає | лише `manifest when:` без read-back | розширення формату без рішення Архітектора | observation, A-14 config-review |
| AI-A12-05 | VP-17 — `ir.default` поля `mrp.bom.consumption` (нові специфікації) | поле на кожній специфікації (A-11) | специфікації, створені кодом з явним `consumption`, ігнорують замовчування | A-11 (AI-A08-27), тур A-16 |
| AI-A12-06 (спроба 2) | VP-02 — галочки `res.config.settings` `group_td_feature_*` (API G0), не прямий запис `implied_ids` | kind `group` спроби 1 | `execute()` знімає групу, якщо галочку зняли, — повторне застосування з іншим VP-02 прибирає функції B у всіх користувачів | read-back B (10 груп) / A, light (0 груп) |
| AI-A12-07 (спроба 2) | Пункт `td_config.alarm_mail_1day` прибрано: нагадування за 1 день постачає `td_mebli_measure` | лишити обидва | у базі спроби 1 лишається зайвий запис нагадування (лише тестові бази, видалені) | read-back AC-004 |
