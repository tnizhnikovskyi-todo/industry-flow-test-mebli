# Архітектура пакета: модулі, залежності, коробки, редакції

Джерело звірки — вихідники Odoo 19.0 CE @ `40e9be2b` (`/home/user/odoo19/src`; шляхи нижче — від цього кореня). EE-модулі в CE присутні лише заглушками `odoo/addons/base/data/ir_module_module.xml` (`mrp_workorder`, `quality_control`, `industry_fsm`, `planning`, `helpdesk`, `sign`, `stock_barcode`, `web_studio`) — їхні моделі й поля **не звірено** (немає доступу до EE, ВП-4).

## 1. Модулі пакета

Позначки: **зріз** — є в базі кроку `8863bf4`; **хвиля 2** — є лише в незавершеній хвилі 2 основного дерева (лише читання); **новий** — з'являється в A-11 за цим ТР.

| Модуль | Статус | Коробка | Призначення (екрани, F-xx) | `depends` (цільові) | Файл ТР |
|---|---|---|---|---|---|
| `td_mebli_base` | **новий** | A | групи ролей і feature-групи коробок, параметри компанії (анкета), шрифт PDF, правила multi-company — спільна основа | `base_setup`, `mail`, `hr` | `td_mebli_base.md`, `security.md` |
| `td_mebli_mrp` | зріз | A | S-03 специфікація замовлення, деталі, правила деталей, імпорт CSV/Excel, норми й розцінки операцій, завантаження дільниць; аналоги (F-57, B) | `td_mebli_base`, `mrp_account`, `stock` | `td_mebli_mrp.md` |
| `td_mebli_sale` | зріз | A | S-02 дати й прогноз, причина зсуву, графік оплат, режим договору, ціна з розмірів, зміна замовлення S-18, візуалізація в КП | `td_mebli_mrp`, `sale_mrp`, `sale_margin`, `sale_purchase_stock`, `purchase_mrp` | `td_mebli_sale.md` |
| `td_mebli_measure` | зріз | A | S-15 замір-лист, ніші, техніка, запис на замір | `td_mebli_sale`, `sale_crm` | `td_mebli_measure.md` |
| `td_mebli_cutting` | зріз | A (пакет, обрізки — B) | S-04 завдання розкрою, порізка в дистриб'ютора, перевірка за заміром, ділові обрізки | `td_mebli_mrp`, `td_mebli_sale`, `td_mebli_measure`, `purchase`, `stock` | `td_mebli_cutting.md` |
| `td_mebli_shop` | зріз | A (кіоск, якість, сканування — B) | S-06 кіоск за PIN, крок якості, S-16 комплектувальний лист, етикетки | `td_mebli_sale`, `hr_hourly_cost`, `sale_stock` | `td_mebli_shop.md` |
| `td_mebli_install` | зріз | A | S-12 акти, недоліки, етапи дошки після «Виготовлено», контроль доплати, денний план; S-17 нарахування | `td_mebli_shop`, `sale_project` | `td_mebli_install.md` |
| `td_mebli_claim` | зріз | A | S-14 рекламація на `repair.order`, повторне виготовлення, платний ремонт | `td_mebli_sale`, `repair` | `td_mebli_claim.md` |
| `td_mebli_cost` | зріз | A | S-11 собівартість план ↔ факт | `td_mebli_sale`, `td_mebli_cutting`, `td_mebli_install` | `td_mebli_cost.md` |
| `td_mebli_purchase` | зріз | A | S-08 ціна проти історії, імпорт прайсу з Excel | `td_mebli_base`, `purchase_stock` | `td_mebli_purchase.md` |
| `td_mebli_ua` | зріз | B (курс) | F-26 курс НБУ; статус обміну BAS переноситься в `td_mebli_bas` | `td_mebli_base`, `sale` | `integrations.md` |
| `td_mebli_bas` | **новий** | A | F-47 обмін з BAS/BAF, табель і нарахування в BAS | `td_mebli_install`, `td_mebli_attendance`, `account` | `integrations.md` |
| `td_mebli_notify` | хвиля 2 | A | F-50 активність зсуву, F-51 листи й нагадування, F-64 брифінг | `td_mebli_dashboard` | `td_mebli_dashboard_notify.md` |
| `td_mebli_dashboard` | зріз | A | S-19 дашборд керівника, табло цеху (F-65, B) | усі функціональні модулі A | `td_mebli_dashboard_notify.md` |
| `td_mebli_maint` | хвиля 2 | A | F-60 верстати ↔ дільниці, простій | `td_mebli_base`, `maintenance`, `mrp` | `td_mebli_hr_maint.md` |
| `td_mebli_attendance` | хвиля 2 | A | F-61 табель з кіоску відвідувань | `td_mebli_base`, `hr_attendance` | `td_mebli_hr_maint.md` |
| `td_mebli_multico` | **новий** | B | F-25 монтаж від іншої юрособи (AI-14) | `td_mebli_install` | `td_mebli_multico.md` |
| `td_mebli_migration` | **новий** | A (шаблони) / B (конвертори) | F-46 конвертори BAS/BAF і БАЗИС у шаблони A-13, звірка | `td_mebli_sale`, `base_import` | `migration.md` |
| `td_mebli_shopfloor` | **новий** міст | C | Shop Floor ↔ кіоск, деталі, причини паузи | `td_mebli_shop`, `mrp_workorder` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_quality` | **новий** міст | C | Quality ↔ крок якості, журнал | `td_mebli_shop`, `quality_control` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_fsm` | **новий** міст | C | Field Service ↔ виїзд і акт | `td_mebli_install`, `industry_fsm` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_planning` | **новий** міст | C | Planning ↔ графік бригад | `td_mebli_install`, `planning` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_helpdesk` | **новий** міст | C | Helpdesk ↔ рекламація | `td_mebli_claim`, `helpdesk` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_sign` | **новий** міст | C | Sign ↔ договір, акт | `td_mebli_install`, `sign` (EE), `auto_install` | `ee-bridges.md` |
| `td_mebli_demo` | зріз | — | демо-дані й показ; клієнтам не ставиться; містить імітацію результату розкрою (AI-A08-15) | усі модулі ядра | — |

**Нові модулі поза зрізом:** `td_mebli_base`, `td_mebli_bas`, `td_mebli_multico`, `td_mebli_migration` + 6 мостів EE.

## 2. Граф залежностей (ядро CE)

```
td_mebli_base ─┬─> td_mebli_mrp ─> td_mebli_sale ─┬─> td_mebli_measure ─> td_mebli_cutting ─> td_mebli_cost (+ td_mebli_install)
               │                                  ├─> td_mebli_shop ─> td_mebli_install ─┬─> td_mebli_multico (B)
               │                                  ├─> td_mebli_claim                     └─> td_mebli_bas <─ td_mebli_attendance
               │                                  └─> td_mebli_migration
               ├─> td_mebli_purchase, td_mebli_ua, td_mebli_maint, td_mebli_attendance
               └─> td_mebli_dashboard (усі функціональні A) ─> td_mebli_notify
мости C: <модуль ядра> + <EE-додаток> ─auto_install─> td_mebli_<міст>
```
Механізм `auto_install` зі списком залежностей — стандарт маніфесту (приклад: `addons/sale_purchase_stock/__manifest__.py:17`, `addons/sale_mrp/__manifest__.py:24`). Правило: ядро не залежить від жодного EE-модуля; AGPL- і OCA-залежностей немає (AI-02); ліцензія `LGPL-3`.

## 3. Як коробки вмикаються (AI-A08-03)

| Механізм | Що робить | Стандарт Odoo 19 |
|---|---|---|
| Feature-групи `td_mebli_base.group_feature_*` | приховують меню, кнопки й поля функцій коробки B у коробці A | галочка налаштування `res.config.settings` з `implied_group` (`odoo/addons/base/models/res_config.py:256`); видимість у поданнях — атрибут `groups` |
| Профіль конфіг-пакета A-12 (`answers.yaml`: VP-01 `light / A / B` + `edition`, функції B — VP-02; SPEC §11) | вмикає/вимикає feature-групи, ставить список модулів | конфіг-пакет (`config-as-code`) |
| Окремі модулі B | `td_mebli_multico`, конвертори `td_mebli_migration` — ставляться лише в B | — |
| Мости C | ставляться самі за наявності EE-додатка | `auto_install` |

| Feature-група | Функції (F-xx) | AC |
|---|---|---|
| `group_feature_configurator` | F-03 | AC-011, AC-012 |
| `group_feature_offcut` | F-11 | AC-059, AC-060 |
| `group_feature_cutting_batch` | F-30 | AC-057, AC-058 |
| `group_feature_kiosk` | F-32, брак у цеху F-18 (варіант 12) | AC-071…AC-073 |
| `group_feature_quality` | F-34, 12-й показник дашборда | AC-074, AC-075, AC-121 |
| `group_feature_label_scan` | F-29 (сканування) | AC-062 |
| `group_feature_change_sign` | F-44 (підпис зміни) | AC-120 |
| `group_feature_nbu` | F-26 | AC-037, AC-038 |
| `group_feature_ai_mapping` | F-27 (AI-підказка) | AC-050 |
| `group_feature_analog` | F-57 | AC-088 |
| `group_feature_shop_board` | F-65 | AC-079 |

Легкий тариф (BOX §1а) — профіль `light`: модулі `td_mebli_base`, `_mrp`, `_sale`, `_measure`, `_cutting` (лише порізка в дистриб'ютора), `_install` (акт без нарахувань — меню нарахувань приховане), `_claim`, `_dashboard`; без `_shop`, `_bas`, `_attendance`, `_maint`. Нового коду немає.

## 4. Редакції

| Позиція | CE (A, B) | EE (C) — головний запис | Міст |
|---|---|---|---|
| Кіоск цеху (F-32) | `td.mebli.kiosk` + `mrp.workcenter.productivity.td_employee_id` | робоче завдання Shop Floor | `td_mebli_shopfloor` |
| Якість (F-34) | `td.mebli.quality.check` | перевірка Quality | `td_mebli_quality` |
| Виїзд і акт (F-38, F-39) | `project.task` + `td.mebli.install.act` | задача Field Service; акт і % бригаді — наші на обох | `td_mebli_fsm`, `td_mebli_planning` |
| Рекламація (F-17) | `repair.order` + поля `td_` | тікет Helpdesk | `td_mebli_helpdesk` |
| Підпис (F-43, F-39) | портал (`sale.order.require_signature`, `addons/sale/models/sale_order.py:112`) і віджет підпису | Sign | `td_mebli_sign` |
| Курс НБУ, графік оплат, версія зміни, комплект, замір, відрядна | наші на обох редакціях (EE їх не дає — `odoo-ecosystem.md` §7.9) | — | — |

## 5. Версії й конвенції

- Версія модулів — `19.0.<major>.<minor>.<patch>`; перший реліз пакета — `19.0.1.1.0` з `migrations/19.0.1.1.0/` для полів, доданих до зрізу (AI-A08-19).
- Моделі — `td.mebli.<сутність>`, поля на стандартних моделях — `td_<поле>` (конвенція зрізу; маска ToDo `td.*`/`td_*` дотримана). Групи — `td_mebli_base.group_<роль>`, імена груп — «Меблі: <роль>».
- Синтаксис 19.0: `<list>`, `invisible`/`readonly`/`required` виразом, `models.Constraint` (`odoo/orm/table_objects.py:79`), `aggregator` (`odoo/orm/fields.py:174`), групи користувача `group_ids` і привілеї `res.groups.privilege` (`odoo/addons/base/models/res_groups_privilege.py:5`, `res_groups.py:36`), зовнішній API — `/json/2` з ключем API (`odoo/addons/test_http/tests/test_webjson2.py:44`). Без `attrs`, `states`, `<tree>`, `t-raw`, `group_operator`, xmlrpc.
- Рядки коду англійською, переклад `i18n/uk.po`; ПДн — лише вигадані в демо.
