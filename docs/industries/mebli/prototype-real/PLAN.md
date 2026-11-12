# План зрізу A-21 (спроба 2) — пакет «меблі» на базі Odoo 19 CE

Дата: 2026-11-12 · гілка `flow/A-21-2-test` · автор: AI (prototype-builder 0.2.1; переробка зразка за 0.2.1 — зворотна перевірка стандарту, §23) · **статус: чернетка, зразок — до рішення людини** (`ACCEPTED.md` ставить людина) ·
`demo_edition: ce` (OWNER-INTAKE) · SHA входів: `413e82a` (OWNER-INTAKE, `concept/*`, `research/*`) · `ODOO_HOME` = `/home/user/odoo19/src` @ `40e9be2b5ab8828bdab450fb6c8c40f2104a36a6` (19.0, 2026-11-10).
Мета: справжні модулі `package/addons/td_mebli_*` (Python + XML + дані), без Studio й полів `x_`, на чистій базі Odoo 19 CE; EE — лише окремою позначкою (`td_mebli_*_ee` з `auto_install`), без EE-залежностей ядра.
Вхід (К-05): `research/FUNCTIONAL-MAP.md` §4.5–4.6, `research/BOX.md` §1, §11.1, §12–13, `research/SALES.md` §2, §4, §6, `research/REUSE.md`, `concept/{features,screens,scenarios}.md` (v2), рішення власника `flow/decisions.md` 23, 30, 31, 35. Попередній зріз (`prototype-real/` і 5 модулів `td_mebli_*` від A-21-real) — **матеріал, не вхід**: код перевикористовується, екрани беруться з концепції v2.
Режим наряду: `params.mode: recalc`, `sample: true` — у цьому запуску зроблено **Крок 1 (цей план, з перевіркою №13 і таблицею «Модель даних»)** і **Крок 2 (зразок: 1 екран, 15 с запису, 1 кадр)**; решта — після приймання зразка.
**Переробка зразка (власник у чаті: «Переделывай сейчас по 0.2.1»; зауваження «зачем закупка в сейл ордере?»).** Попередній зразок мав модель `td.mebli.order.item` у замовленні на продаж із ручним постачальником і датою — паралельний облік закупівлі (за 0.2.1 — FAIL). Тепер замовні позиції купує стандарт (MTO + «Купити» → замовлення на купівлю), дату постачальника вводять лише в модулі Закупівлі, `td_` лише читає й рахує (таблиця «Модель даних» нижче).

## 1. Що показуємо (зв'язок із концепцією)

**Наскрізний сценарій (SALES §6, 20–25 хв):** одне замовлення «кухня + шафа-купе» в одному договорі. Замірник вносить ніші й техніку, система підсвічує невміщення (сцена 1); менеджер підбирає шафу в конфігураторі, ціна з розмірів іде в рядок (1а); імпорт специфікації з CSV, маржа до запуску, графік оплат, підпис версії (2); клієнт змінює фасади — нова версія, ціна, дата, причина «клієнт» (3); фарбовані фасади від постачальника запізнюються — прогнозна дата пізніша за обіцяну, причина «постачальник» (4, NG-01 у коробці A — запис 31); цех за PIN «Взято / Зроблено», комплектувальний лист не відпускає неповний комплект (5); пакет розкрою за декором, ділові обрізки, крок якості з фото (5а); два виїзди монтажу з актом і % бригаді (6); рекламація й собівартість план ↔ факт (7); дашборд керівника (8).

| S-xx (екран брифу) | Сцени SALES §6 | Що входить у зріз | Чим закрито |
|---|---|---|---|
| S-15 Замір-лист (1) | 1 | ніші, техніка, фото, перевірка «не вміщається» | стандарт CRM (заявка → зустріч, F-48) + `td_` модель заміру на замовленні |
| S-02 Замовлення клієнта (2) | 1а, 2, 4 | ціна з розмірів, маржа до запуску, графік оплат, **обіцяна/прогнозна дата, закупівлі під замовлення (лише читання), причина зсуву** (зразок), статус обміну з BAS (імітація) | стандарт `sale_margin`, `sale_mrp`, `commitment_date`, `sale_purchase_stock` (закупівлі замовлення) + `td_mebli_sale` (лише compute) |
| S-01 Конфігуратор (3) | 1а | модель, розміри, декор, фурнітура, кромка; правила сумісності | стандартний конфігуратор атрибутів + `td_mebli_sale` (розміри), правила — `td_` |
| S-03 Специфікація (4) | 2 | деталі Д×Ш×Т, матеріал, кромка; імпорт CSV з розпізнаванням колонок; версія | `td_mebli_mrp` (деталі, BoM замовлення) + `td_` імпорт; CAD — лише CSV-вивантаження (імітація формату) |
| S-04 Розкрій і порізка (5) | 5а | пакет розкрою кількох МО за декором, вкладка «Ділові обрізки», замовлення порізки | `td_mebli_cutting`; **імітацію оптимізатора не показуємо** (OUT-02) |
| S-05 Дошка замовлень (6) | 3, 4 | етапи, обіцяна й прогнозна дата, причина зсуву, «очікує клієнта» | канбан `td_mebli_sale` (є) + поля зразка |
| S-06 Планшет цеху (7) | 5, 5а | робочі завдання дільниць, «Взято / Зроблено / Пауза з причиною», кіоск за PIN, крок якості з фото, завантаження | стандарт робочих замовлень `mrp` + `td_` кіоск і точки якості (див. §2, №13) |
| S-08 Дефіцит і прайси (8) | 4, 8 | нестача під замовлення, замовні позиції, ціна постачальника проти історії | стандарт `purchase_stock` (MTO, прайси постачальника) + `td_` звіт «ціна ↔ історія» |
| S-16 Комплектувальний лист (9) | 5 | місця, деталі, зібрано / бракує, блок відвантаження | стандарт складу + `td_` лист і перевірка комплекту |
| S-12 Календар монтажів і акт (10) | 6, 8 | виїзди бригад (календар без Ганта), акт з фото, підписом і недоліками, фотоархів | стандарт `project` (календар задач) + `td_` акт |
| S-17 Нарахування (11) | 6, 8 | відрядна за операціями, % бригаді з акта, премії й штрафи з причиною | `td_` (Payroll — лише EE і без України, FM §4.5) |
| S-14 Рекламація (12) | 7 | реєстрація, повторне виготовлення / ремонт | стандарт `repair` + `td_` зв'язок із замовленням і деталлю |
| S-11 Собівартість план ↔ факт (13) | 7 | план і факт по замовленню | стандарт аналітики МО (див. §2, №13) + адаптований `td_sale_cost` (REUSE-01) |
| S-18 Погодження й зміна (15) | 2, 3 | версія на підпис, зміна з ціною, датою й причиною | стандарт порталу й підпису пропозиції + `td_` версія специфікації |
| S-19 Дашборд керівника (16) | 8 | 11 показників коробки A (BOX §11.1 KPI 1–10 + ціни постачальників), картка = звіт drill-down | `td_mebli_dashboard` (клієнтська дія; переписати під KPI BOX §11.1) |

**Поза зрізом (свідомо; піде в README «Відкинуто»):** імітація оптимізатора розкрою (OUT-02, SALES §6); мости EE (`_shopfloor`, `_quality`, `_fsm`, `_helpdesk`, `_sign`, `_planning`) — немає доступу до EE, ризик R-14 «не змішувати інтерфейси»; рядок «невідповідності якості» на S-19 — лише B / C (BOX §11.1); справжній обмін з BAS/BAF (F-47) — у зрізі лише статус обміну як імітація; пакет міграції (F-46, D-10) і кілька юросіб з ПРРО (F-25, C-03) — не екрани (R18); кабінет покупця (REJ-017), портал D-08, маржа за курсом EUR (REJ-018) — відкидання підтверджено (запис 34); претензія постачальнику порізки D-17 — після A-06 (запис 34).

**Зразок (Крок 2):** S-02 «Замовлення клієнта» — блок дат, банер і вкладка «Закупівлі під замовлення» (рядки стандартних замовлень на купівлю, лише читання; смарт-кнопка «Купівлі» модуля `sale_purchase`) (F-23, F-31, F-36; SC-01.7; NG-01). Чому цей екран першим: це **варіант цінності 1** («Дата, яку ви обіцяли клієнту, — під контролем: видно, що її зірве, до того як зірве», SALES §4), відповідь на заперечення 5 «Нам вистачає Excel і Viber» (SALES §2), єдиний біль ROLE-02 із прямою цитатою (PAIN-16 «Обіцяли два місяці, вийшло три») і коробка A (запис 31). Дашборд S-19 як зразок відкладено: 7 з 11 його показників спираються на екрани, яких у зрізі ще немає (замір, акт, рекламація, нарахування), — зразок показав би заглушки.

## 2. Стандарт Odoo 19, на який спираємось (перевірено у вихідниках 19.0 CE @ `40e9be2b`)

| Припущення | Підтвердження (файл:рядок) | Як використовуємо |
|---|---|---|
| Обіцяна клієнту дата — стандартне поле замовлення | `addons/sale/models/sale_order.py:88` (`commitment_date`, help «delivery date promised to the customer»); очікувана дата `:302` | «Обіцяна дата» на S-02 і S-05 — це `commitment_date` з власним підписом у поданні; на формі одне поле: стандартне (`addons/sale_stock/views/sale_order_views.xml:36`) переміщено (`position="move"`) з «Іншої інформації» до прогнозної дати, не додано вдруге |
| Тривалість виробництва — стандартне поле специфікації; кінець МО рахується від нього | `addons/mrp/models/mrp_bom.py:89` (`produce_delay`); `addons/mrp/models/mrp_production.py:786-795` (`_compute_date_finished`), `:255` (`is_planned`) | готовність цеху = кінець МО (запланованих робочих замовлень або `date_start + produce_delay`) |
| Замовлення продажу бачить свої МО | `addons/sale_mrp/models/sale_order.py:14` (`mrp_production_ids`) | прогнозна дата й етап дошки |
| Маржа замовлення до підтвердження | `addons/sale_margin/models/sale_order.py:11` (`margin_percent`) | маржа на S-02 (планова собівартість — з BoM замовлення `td_mebli_sale`) |
| Купівля під замовлення (MTO + «Купити») — стандарт; постачальник і його строк — у прайсі постачальника | маршрути `addons/stock/data/stock_data.xml:42` (`route_warehouse0_mto`), `addons/purchase_stock/data/purchase_stock_data.xml:10` (`route_warehouse0_buy`); правило купівлі `addons/purchase_stock/models/stock_rule.py:59` (`_run_buy`); прайс `addons/product/models/product_supplierinfo.py:13` (`partner_id`), `:51` (`delay`) | замовні позиції (фасади фарбовані, стільниця, профіль купе) — товари з маршрутами MTO + «Купити» і рядком `product.supplierinfo`, компоненти специфікації; підтвердження замовлення на продаж → МО → замовлення на купівлю (перевірено тестом `test_confirmation_creates_the_purchase_by_the_standard`) |
| Дата постачальника — рядок замовлення на купівлю (ввід лише в модулі Закупівлі) | `addons/purchase/models/purchase_order_line.py:25` (`date_planned`), `:72` (`qty_received`), `:91` (`partner_id`) | прогнозна дата S-02 читає `date_planned` і `qty_received`; у `sale.order` дата не вводиться |
| Зв'язок замовлення на продаж ↔ закупівлі в 19.0 — через `stock.reference` (не procurement group) | `addons/sale_stock/models/sale_order.py:48` (`stock_reference_ids`); значення закупівлі несуть `reference_ids` з руху МО `addons/stock/models/stock_move.py:1843`, `:1877`; закупівля успадковує їх `addons/purchase_stock/models/stock_rule.py:117-121`; нова закупівля отримує `reference_ids` у `_prepare_purchase_order` — `addons/purchase_stock/models/stock_rule.py:355`; злиття запитів зберігає посилання обох — `addons/purchase_stock/models/purchase_order.py:478` (`_merge_po_post_process`); поле `addons/purchase_stock/models/purchase_order.py:28`; `addons/purchase_stock/models/stock_reference.py:7` (`purchase_ids`); `addons/sale_purchase/models/sale_order.py:54` + `addons/sale_purchase_stock/models/sale_order.py:14` (`_get_purchase_orders` = рядки сервісів ∪ `stock_reference_ids.purchase_ids`) | вкладка S-02 = `_get_purchase_orders().order_line`, відфільтровані до рядків, що живлять МО цього замовлення (compute, лише читання); правило доступу «закупівлі моїх замовлень» — за тим самим `reference_ids.sale_ids` |
| Закупівля живить компонент МО | `addons/purchase_stock/models/purchase_order_line.py:30` (`move_dest_ids`), `addons/mrp/models/stock_move.py:33` (`raw_material_production_id`); `addons/purchase_mrp/models/mrp_production.py:46` (`_get_purchase_orders` МО); ланцюг руху при прийманні у 2–3 кроки — `addons/stock/models/stock_move.py:2697` (`_rollup_move_dests`), так само читає `addons/purchase_mrp/report/mrp_report_mo_overview.py:23` (тест `test_two_step_receipt_follows_the_chain`) | «готовність за позицією» = `date_planned` + `produce_delay` специфікації МО, що споживає позицію |
| Смарт-кнопка закупівель на замовленні на продаж — стандарт | `addons/sale_purchase/models/sale_order.py:10` (`purchase_order_count`, група `purchase.group_purchase_user`), `addons/sale_purchase/views/sale_order_views.xml:15`; `sale_purchase_stock` — `auto_install` (`addons/sale_purchase_stock/__manifest__.py:12,17`) | кнопка «Купівлі» лишається закупівельникам (стандарт); менеджер салону групи «Закупівлі» не має — читає закупівлі своїх замовлень на вкладці (правило `td_mebli_sale`) |
| «Днів на обробку» після отримання позиції — стандартний аналог `produce_delay` | `addons/mrp/models/mrp_bom.py:89` (`produce_delay`, час виготовлення від старту МО); `:92` (`days_to_prepare_mo` — дні на збір компонентів ДО старту, інший зміст); стандартне планування МО вважає, що компоненти потрібні на старті (`addons/mrp/models/mrp_production.py:786`) | нового поля немає: готовність за позицією = дата поставки + `produce_delay` специфікації замовлення (специфікація замовлення копіює `produce_delay`/`days_to_prepare_mo` шаблону — `td_mebli_mrp`) |
| Аналітика на виробничих замовленнях у CE | `addons/project_mrp/models/mrp_production.py:9` (`project_id`); `addons/project_mrp_account/models/mrp_production.py:10-16`; `addons/mrp_account/models/mrp_workorder.py:10` (`mo_analytic_account_line_ids`); `addons/project_mrp_account/models/mrp_workorder.py:9-14`; категорія `manufacturing_order` — `addons/mrp_account/models/analytic_account.py:79` | S-11 план ↔ факт: проєкт замовлення з аналітичним рахунком → рядки аналітики з робіт МО (тест №13 нижче) |
| Календар задач у CE — без Ганта | `addons/project/views/project_task_views.xml:829` (`<calendar date_start="date_deadline" …>`); типи подань `odoo/addons/base/models/ir_ui_view.py:149-153` — `gantt` немає; каталогу `addons/web_gantt` у 19.0 CE немає | S-12: графік бригад — календар задач `project` або наш список |
| Час на робочому замовленні в CE пишеться на користувача, не на працівника | `addons/mrp/models/mrp_workcenter.py:531` (`mrp.workcenter.productivity.user_id`); `addons/mrp/models/mrp_workorder.py:122` (`working_user_ids`) | кіоск цеху за PIN без користувача Odoo — `td_` (див. №13) |
| Вхід за PIN без користувача в CE є лише для кіоску відвідувань | `addons/hr/models/hr_employee.py:211` (`pin`); `addons/hr_attendance/models/res_company.py:34` (`attendance_kiosk_use_pin`); `addons/hr_attendance/controllers/main.py:139` (`auth='public'`), `:203-208` (перевірка PIN) | взірець для `td_` кіоску цеху (працівник `hr.employee` без користувача) |
| Модулі Shop Floor, Quality, Studio, Sign, Field Service, Planning, Helpdesk — лише EE | `odoo/addons/base/data/ir_module_module.xml:257` (`mrp_workorder`), `:131` (`quality_control`), `:5` (`web_studio`), `:187` (`sign`), `:61` (`industry_fsm`), `:159` (`planning`), `:75` (`helpdesk`) — записи-заглушки з `to_buy`, у базі CE стан `uninstallable`, ліцензія OEEL-1 | у ядрі не залежимо; мости — окремі `td_mebli_*_ee` |
| Автоматичного курсу валют (і НБУ) у CE немає | у `addons/` 19.0 CE немає `currency_rate_live` (і заглушки в `ir_module_module.xml`); у базі CE з `l10n_ua` немає полів постачальника курсу в `res.company` і cron курсу; модель курсу — `odoo/addons/base/models/res_currency.py:346-347` | F-26 курс НБУ — `td_` (завантаження курсу в `res.currency.rate`); у зрізі — імітація без мережі |
| Набір дашбордів CE — `spreadsheet_dashboard` + 12 тематичних, виробничого немає | каталоги `addons/spreadsheet_dashboard*` (13), `spreadsheet_dashboard_mrp` відсутній; редагування таблиць (`spreadsheet_edition`) — не в CE | S-19 — власна клієнтська дія `td_mebli_dashboard` |
| Адаптивний інтерфейс і підпис пальцем — у веб-клієнті CE | `addons/web/static/src/core/ui/ui_service.js:154` (`isSmall`); `addons/web/static/src/views/fields/signature/signature_field.js:14` | екрани 1, 7, 10 на телефоні — стандартний мобільний UI; `web_responsive` не потрібен (рішення №14 відкрите) |
| Конвенції 19.0 | `odoo/orm/table_objects.py:79` (`models.Constraint`); `odoo/addons/base/models/res_users.py:257` (`group_ids`), `:247` (`company_ids`); `odoo/addons/base/models/res_groups.py:36` (`privilege_id`) | код зрізу: `models.Constraint`, `group_ids`, без `attrs=`/`states=`, корінь list-view `<list>` |
| Ремонт і проєкти — CE, LGPL-3 | `addons/repair/__manifest__.py:52`, `addons/project/__manifest__.py:250`, `addons/hr_attendance/__manifest__.py:96` | S-14 на `repair`, S-12 на `project`, кіоск — за зразком `hr_attendance` |

EE-твердження: окремого `research/edition-claims.md` немає (див. `concept/screens.md`); у цьому плані EE не обіцяється як факт — «не перевірено».

### Не перевірено вихідниками і закрито тестом
- Ланцюг «замовлення на продаж → МО → компонент MTO + «Купити» → замовлення на купівлю, пов'язане із замовленням на продаж» — тест модуля `td_mebli_sale/tests/test_order_dates.py` (7 сценаріїв: пропозиція — вирішує цех; підтвердження створює закупівлю стандартом і смарт-кнопка її рахує; пізня `date_planned` зсуває прогноз — причина «Постачальник»; отримана позиція не зсуває; цех пізніше — «Компанія»; продавець без прав на закупівлі бачить прогноз і причину; поля дат лише compute/readonly, моделі `td.mebli.order.item` немає) і база показу `demo-mebli-sample` (3 закупівлі `P00001…3` створено підтвердженням замовлення S00123).
- Причина «Клієнт» (зміна на прохання клієнта) прибрана зі зразка: ручний ввід причини в `sale.order` не потрібен для показу сцени 4; джерело для неї — версія пропозиції/зміна (S-18, повний обсяг).

### Перевірка №13 (CE) — рішення власника №13, записи 30, 35
Чиста база `demo-check13` (Odoo 19.0 CE @ `40e9be2b`, без демо-даних; модулі `mrp_account`, `project_mrp_account`, `project`, `hr_attendance`, `l10n_ua`, `sale_management`, `purchase_stock`, `sale_margin`, `repair`). Перевірка — запитами `odoo-bin shell` і HTTP/Playwright до локального сервера. EE — доступу немає.

| Пункт №13 | CE: як перевірено | CE: статус | EE |
|---|---|---|---|
| Аналітика на виробничих замовленнях без EE | створено аналітичний план і рахунок, проєкт з рахунком, МО з `project_id` і операцією; робоче замовлення 1 год на дільниці з вартістю години → `has_analytic_account = True`, 1 рядок аналітики МО на суму роботи (від'ємна, витрата) | **підтверджено** | не перевірено (EE) |
| Календар задач CE без Ганта | типи подань `project.task` у базі: activity, calendar, form, graph, kanban, list, pivot, search; типу `gantt` у `ir.ui.view` немає | **підтверджено** (календар є, Ганта немає) | Гант / Planning — не перевірено (EE) |
| Кіоск цеху за PIN без користувача Odoo | `hr.employee.pin` є, `user_id` працівника необов'язковий; кіоск відвідувань `/hr_attendance/<ключ>` відкривається без сесії (HTTP 200); але час робочого замовлення пишеться лише на `res.users` (`mrp.workcenter.productivity.user_id`), полів працівника в `mrp.workorder` немає | **не підтверджено** для цеху (у CE лише кіоск відвідувань) → `td_` кіоск, чутливість FM §4.6 «+40–80» до години A-08 | Shop Floor за PIN — не перевірено (EE) |
| Курс НБУ в CE | модулів автоматичного курсу в CE немає, полів постачальника курсу й cron у базі з `l10n_ua` немає | **не підтверджено** (стандарту немає) → `td_` F-26 | `currency_rate_live` — не перевірено (EE) |
| Телефон і планшет | Playwright 390×844, `isMobile`, DPR 3, вхід адміністратором: задачі й МО відкриваються мобільним канбаном, бургер-меню є, горизонтальної прокрутки немає, помилок консолі немає | **підтверджено** (веб-клієнт); камера, підпис пальцем, слабкий зв'язок на пристрої — **не перевірено** (немає пристрою) | не перевірено (EE) |
| Онлайн-оплата українськими картками | сторонній модуль, мережі до платіжних систем немає | не перевірено | не перевірено |
| Наш екран сканування поруч із Barcode EE | Barcode — EE | не перевірено (EE-частина) | не перевірено |

Висновок для годин A-08: два пункти «лише CE» не підтвердились (кіоск за PIN для цеху, курс НБУ) — їхні рядки лишаються `td_` з верхньою межею годин; аналітика МО і календар без Ганта підтверджені — S-11 і S-12 спираються на стандарт.

### REUSE-01 `td_sale_cost` (план; у зразок не входить)
Код: `repo:tnizhnikovskyi-todo/todo_timur/factory3d/odoo_addons/td_sale_cost@0976f05` (версія `19.0.1.1.1`, LGPL-3, `depends: sale_mrp, td_factory3d`, `auto_install`).
Сумісність з 19.0 CE: `sale_mrp` — CE; жорстка прив'язка до `td_factory3d` — `depends` і група `td_factory3d.group_td_manager` у `views/sale_order_views.xml:12, 33-42`, `models/td_sale_cost.py:15, 57`; статті «енергія / верстати» (`models/td_sale_cost_calc.py:134-145, 193-229`) працюють лише за наявності модулів Factory 3D. План адаптації (`REUSE.md`: 16–32 за оцінкою): копія в `td_mebli_cost` (LGPL-3 сумісна), група — власна `td_mebli`, статті енергії й верстатів прибрати, додати статтю «порізка» й «відрядна / % бригаді», тести `tests/test_calc.py`, `test_cost.py` перенести. Ризик: оцінку AI не перевірено установкою на чистій базі — у A-11.

### Модель даних (зворотна перевірка стандарту, §23)
Охоплення — усі `package/addons/td_mebli_*` (вивід `check_data_model.py`: нові `td.*`-моделі й поля на стандартних моделях). Питання до кожного рядка: чи не дублює це дані, які веде стандартний модуль? Шляхи — від `ODOO_HOME/addons/` (19.0 CE @ `40e9be2b`). Ввід, якого немає в стандарті, позначено «ввід»; усе інше — compute/related (лише читання).

**Зразок S-02 (`td_mebli_sale`, переробка за 0.2.1)**

| Модель / поле | Нова чи розширення (`_inherit`) | Стандартний аналог (файл:рядок 19.0) | Чому не стандарт |
|---|---|---|---|
| `td.mebli.order.item` | **видалено** | закупівля під замовлення: `stock/data/stock_data.xml:42` + `purchase_stock/data/purchase_stock_data.xml:10` (MTO + «Купити»), `purchase/models/purchase_order_line.py:25` (`date_planned`), `product/models/product_supplierinfo.py:13` | паралельний облік закупівлі в замовленні на продаж (FAIL за 0.2.1) — модель прибрано, дані веде модуль Закупівлі |
| `sale.order.td_purchase_line_ids` | розширення, compute (не збережене), лише читання; групи — продавець і закупівельник | `sale_purchase/models/sale_order.py:54` + `sale_purchase_stock/models/sale_order.py:14` (`_get_purchase_orders`) — читаємо їхні `order_line`, лише рядки, що живлять МО цього замовлення (`move_dest_ids` → `_rollup_move_dests` `stock/models/stock_move.py:2697` → `raw_material_production_id`; злиття запитів — `purchase_stock/models/purchase_order.py:478`) | — |
| `sale.order.td_shop_date` | розширення, compute | `mrp/models/mrp_production.py:786` (`_compute_date_finished`), `mrp/models/mrp_bom.py:89` (`produce_delay`); `sale_mrp/models/sale_order.py:14` (`mrp_production_ids`) | — |
| `sale.order.td_forecast_date` | розширення, compute | `purchase/models/purchase_order_line.py:25` (`date_planned`, читаємо) + `td_shop_date` | — |
| `sale.order.td_delay_days` | розширення, compute | `sale/models/sale_order.py:88` (`commitment_date`) проти прогнозної дати | — |
| `sale.order.td_late_line_id` | розширення, compute; групи — продавець і закупівельник | рядок із `_get_purchase_orders()` (`sale_purchase/models/sale_order.py:54`) | — |
| `sale.order.td_late_item` | розширення, compute | `purchase/models/purchase_order_line.py:91` (`partner_id`) + товар рядка (читаємо) | — |
| `sale.order.td_delay_reason` | розширення, compute (не збережене; ручного «клієнт» більше немає) | немає (у стандарті причини зсуву дати немає) | вибір «Постачальник / Компанія» виводиться з дат закупівлі й МО, не вводиться |
| `purchase.order.line.td_date_ready` | розширення, compute | `purchase/models/purchase_order_line.py:25` (`date_planned`), `:72` (`qty_received`), `mrp/models/mrp_bom.py:89` (`produce_delay` специфікації МО через `purchase_stock/models/purchase_order_line.py:30` `move_dest_ids` → `mrp/models/stock_move.py:33`) | — |

**Права S-02 (рецензія Архітектора, коло 1).** Менеджер салону (`sales_team.group_sale_salesman`) не має групи «Закупівлі». `td_mebli_sale/security/ir.model.access.csv` дає продавцю лише читання `purchase.order` і `purchase.order.line` (без write/create/unlink); `security/purchase_security.xml` — правила: продавець — «закупівлі моїх замовлень» (`reference_ids.sale_ids.user_id = user`, той самий зв'язок, що й `_get_purchase_orders`), «Усі документи» — закупівлі будь-якого замовлення, групи, які за стандартом уже читають усі закупівлі (Закупівлі, Склад, Облік — `purchase/security/ir.model.access.csv`, `purchase_stock/security/ir.model.access.csv`), — без обмеження (правила груп у Odoo поєднуються через АБО). Вкладку «Закупівлі під замовлення» бачать продавець і закупівельник; смарт-кнопка `sale_purchase` — лише закупівельник (стандарт). `sudo` у compute — лише читання: `_td_purchase_lines` (рядки закупівель і МО замовлення, щоб прогноз і причину бачив будь-який продавець), `_td_productions` (рухи складу, яких продавець не читає), `produce_delay` специфікації; у поля віддаються записи без `sudo` (`sudo(False)`), тож рядки вкладки браузер читає з правами продавця; запису через `sudo` немає. Інверсія `td_stage` — без `sudo`, лише для `mrp.group_mrp_user`. Перевірено тестами `test_salesperson_reads_the_purchases_of_his_orders_only`, `test_stage_drag_needs_manufacturing_rights`.

**Решта пакета (попередній зріз, у зразку без змін — для повноти охоплення скрипта)**

| Модель / поле | Нова чи розширення (`_inherit`) | Стандартний аналог (файл:рядок 19.0) | Чому не стандарт |
|---|---|---|---|
| `sale.order.td_launch_date` | розширення, compute | `mrp/models/mrp_workcenter.py:531` (`mrp.workcenter.productivity`, `date_start` — читаємо) | — |
| `sale.order.td_hours_to_launch` | розширення, compute | `sale/models/sale_order.py` `date_order` + час робіт МО (читаємо) | — |
| `sale.order.td_production_count` | розширення, compute | `sale_mrp/models/sale_order.py:14` (`mrp_production_ids`) | — |
| `sale.order.td_stage` | розширення, compute (збережене для групування дошки), inverse лише викликає стандартний `button_start` — з правами самого користувача (без `sudo`) і лише для групи `mrp.group_mrp_user`; продавцю — помилка, кнопка «Почати» лишається в МО | `sale/models/sale_order.py:71` (`state`), `mrp/models/mrp_production.py:177` (`state`) | етап дошки виводиться зі станів замовлення й МО; ручного вводу етапу немає (inverse відмовляє в усьому, крім «почати роботу») |
| `sale.order.td_image` | розширення, compute | `image_256` товару першого рядка (читаємо) | — |
| `sale.order.line.td_is_parametric` | розширення, related/compute | `td_is_parametric` товару (читаємо) | — |
| `sale.order.line.td_width` | розширення, compute | `product/models/product_attribute_custom_value.py:17` (`custom_value`, читаємо) | — |
| `sale.order.line.td_height` | розширення, compute | `product/models/product_attribute_custom_value.py:17` | — |
| `sale.order.line.td_depth` | розширення, compute | `product/models/product_attribute_custom_value.py:17` | — |
| `sale.order.line.td_size_factor` | розширення, compute | немає | коефіцієнт ціни від розмірів — у стандарті ціна лише від варіанта й доплат |
| `sale.order.line.td_bom_id` | розширення, ставить система (специфікація замовлення) | `sale_mrp/models/mrp_production.py:14` (`sale_line_id` МО); специфікацію МО шукає `mrp/models/mrp_bom.py` `_bom_find` | у стандарті немає специфікації на рядок замовлення (параметричний виріб за розмірами клієнта) |
| `sale.order.line.td_planned_material_cost` | розширення, compute | `sale_margin/models/sale_order_line.py:15` (`purchase_price`) — розклад тієї самої собівартості | — |
| `sale.order.line.td_planned_operation_cost` | розширення, compute | `sale_margin/models/sale_order_line.py:15` | — |
| `mrp.bom.td_sale_line_id` | розширення, ставить система | `sale_mrp/models/mrp_production.py:14` (`sale_line_id` — на МО, не на специфікації) | зв'язок специфікації замовлення з рядком продажу; у стандарті специфікації замовлення немає |
| `mrp.bom.td_sale_order_id` | розширення, related | `td_sale_line_id.order_id` | — |
| `mrp.production.td_partner_id` | розширення, compute | `mrp/models/stock_reference.py:7` (`production_ids` ↔ `sale_ids`), `sale_mrp/models/mrp_production.py:14` | — |
| `mrp.bom.td_order_bom` | розширення, ставить система | немає | ознака специфікації одного замовлення (параметричний виріб) |
| `mrp.bom.td_template_bom_id` | розширення, ставить система | немає | посилання специфікації замовлення на шаблон |
| `mrp.bom.td_width` | розширення, ставить система | немає (розмірів у `mrp.bom` немає) | розміри виробу замовлення |
| `mrp.bom.td_height` | розширення, ставить система | немає | розміри виробу замовлення |
| `mrp.bom.td_depth` | розширення, ставить система | немає | розміри виробу замовлення |
| `mrp.bom.td_part_ids` | розширення | немає (деталей Д×Ш×Т у стандарті немає) | деталі розкрою — сутність без аналога |
| `mrp.bom.td_part_count` | розширення, compute | — | підсумок деталей |
| `mrp.bom.td_board_area_m2` | розширення, compute | — | підсумок площі плити з деталей |
| `mrp.bom.td_edge_length_m` | розширення, compute | — | підсумок кромки з деталей |
| `td.mebli.part` | нова | немає | деталь розкрою (Д×Ш, матеріал, кромка) — у стандарті немає |
| `td.mebli.part.rule` | нова | немає | правило деталі параметричного виробу від розмірів |
| `mrp.routing.workcenter.td_time_basis` | розширення, ввід | `mrp/models/mrp_routing.py:27` (`time_mode`: вручну / за фактом) | база нормування «на деталь / на м кромки / на м² плити» — у стандарті немає |
| `mrp.routing.workcenter.td_time_rate` | розширення, ввід | `mrp/models/mrp_routing.py:33` (`time_cycle_manual` — хвилин на виріб; його й заповнюємо в специфікації замовлення) | норма на одиницю бази (деталь, м, м²) — у стандарті немає |
| `mrp.workcenter.td_capacity_hours` | розширення, **compute без store** (ввід прибрано) | `mrp/models/mrp_workcenter.py:81` (`resource_calendar_id` → `resource/models/resource_calendar.py:104` `hours_per_week`) × паралельність (`:78` `capacity_ids`, потужність без товару; як `_get_capacity` `:427`); `time_efficiency` не множимо — вона вже в `duration_expected` (`mrp/models/mrp_workorder.py:847`) | — (лише підсумок стандартних даних для %; у стандарті поля «годин на тиждень» дільниці немає) |
| `mrp.workorder.td_expected_hours` | розширення, compute | `mrp/models/mrp_workorder.py:88` (`duration_expected`, читаємо) | — |
| `mrp.workorder.td_load_pct` | розширення, compute | `duration_expected` проти потужності дільниці; у звіті сумується за дільницею й тижнем `date_start` (`interval="week"` у graph/pivot) | — |
| `mrp.workorder.td_load_stage` | розширення, compute | — | групування завантаження |
| `mrp.workorder.td_load_zone` | розширення, compute | сума відкритих годин — стандартне `workcenter_load` (`mrp/models/mrp_workcenter.py:67`, `_compute_workorder_count` `:169`) проти `td_capacity_hours` | зона «понад потужність» (у стандарті ознаки немає; потрібна для групування) |
| `mrp.production.td_cutting_job_ids` | розширення | немає | зв'язок МО з пакетом розкрою (сутність без аналога) |
| `mrp.production.td_cutting_job_count` | розширення, compute | — | лічильник |
| `td.mebli.cutting.job` | нова | немає (розкрою в CE немає) | пакет розкрою кількох МО за декором |
| `td.mebli.cutting.sheet` | нова | `stock/models/stock_lot.py:42` (лист = партія; посилаємось на `stock.lot`, не дублюємо) | аркуш у пакеті розкрою |
| `td.mebli.cutting.placement` | нова | немає | розміщення деталі на аркуші |
| `td.mebli.cutting.offcut` | нова | `stock/models/stock_lot.py:42` (обрізок обліковується партією `stock.lot`) | рядок результату розкрою; запас обрізка — у стандартній партії |
| `stock.lot.td_length_mm` | розширення, ввід | немає (розмірів у `stock.lot` і `product.template` немає: `product/models/product_template.py:112-115` — лише об'єм і вага; розміри — лише `stock/models/stock_package_type.py:22-23`) | розмір листа/обрізка — дані без аналога |
| `stock.lot.td_width_mm` | розширення, ввід | немає (див. рядок вище) | розмір листа/обрізка |
| `stock.lot.td_is_offcut` | розширення, ввід | немає | ознака ділового обрізка |
| `stock.lot.td_cutting_job_id` | розширення | немає | з якого розкрою обрізок |
| `stock.lot.td_area_m2` | розширення, compute | — | площа з розмірів |
| `stock.lot.td_reserved_m2` | розширення, compute | — | резерв під розкрій |
| `stock.lot.td_reserved_for` | розширення, compute | — | для якого розкрою резерв |
| `td.mebli.dashboard` | нова | `spreadsheet_dashboard` (CE, 13 тематичних, виробничого немає) | екран керівника з KPI коробки A — клієнтська дія |
| `product.template.td_is_parametric` | розширення, ввід | немає | ознака параметричного виробу |
| `product.template.td_width_nominal` | розширення, ввід | немає (розмірів товару в CE немає) | номінальні розміри виробу |
| `product.template.td_height_nominal` | розширення, ввід | немає | номінальні розміри |
| `product.template.td_depth_nominal` | розширення, ввід | немає | номінальні розміри |
| `product.template.td_width_min` | розширення, ввід | немає | допустимий діапазон розмірів |
| `product.template.td_width_max` | розширення, ввід | немає | допустимий діапазон |
| `product.template.td_height_min` | розширення, ввід | немає | допустимий діапазон |
| `product.template.td_height_max` | розширення, ввід | немає | допустимий діапазон |
| `product.template.td_depth_min` | розширення, ввід | немає | допустимий діапазон |
| `product.template.td_depth_max` | розширення, ввід | немає | допустимий діапазон |
| `product.template.td_edge_allowance_mm` | розширення, ввід | немає | припуск кромки |
| `product.template.td_part_rule_ids` | розширення | немає | правила деталей |
| `product.template.td_material_kind` | розширення, ввід | немає (є лише категорія товару) | вид матеріалу (плита / кромка / фурнітура / готовий фасад) для розкрою; «готовий фасад» — рядок шаблонної специфікації з «Застосувати до варіантів» (`mrp/models/mrp_bom.py:777` `_skip_bom_line`) замінює правило деталі «Фасад»: фасади не рахуються двічі |
| `product.template.td_sheet_length_mm` | розширення, ввід | немає | формат листа плити |
| `product.template.td_sheet_width_mm` | розширення, ввід | немає | формат листа плити |
| `product.template.td_thickness_mm` | розширення, ввід | немає | товщина плити |
| `product.template.td_waste_pct` | розширення, ввід | немає (у рядку специфікації немає % відходу) | норма відходу розкрою |
| `product.template.td_matches_board_id` | розширення, ввід | немає | кромка до декору плити |
| `product.template.td_edge_thickness` | розширення, ввід | немає | товщина кромки |
| `product.attribute.td_dimension` | розширення, ввід | `product/models/product_attribute.py:24` (`create_variant`); власне значення — `product_attribute_custom_value.py:17` | який розмір задає атрибут (ширина / висота / глибина) |
| `product.attribute.td_component_role` | розширення, ввід | `mrp/models/mrp_bom.py:777` (`_skip_bom_line` за значеннями атрибутів) | роль значення (декор корпусу / фасаду / кромка / фурнітура) як параметр деталей розкрою, не лише рядок специфікації |
| `product.attribute.value.td_component_product_id` | розширення, ввід | `mrp/models/mrp_bom.py:777` (рядок специфікації за значенням атрибута) | значення атрибута → матеріал деталей (площа рахується з розмірів), не фіксована кількість рядка |
| `product.attribute.value.td_edge_thickness` | розширення, ввід | немає | товщина кромки значення |

## 3. Модулі

Граф (стрілка — `depends`; лише CE): `mrp_account, stock` → **`td_mebli_mrp`** → **`td_mebli_sale`** (`+ sale_mrp, sale_margin`) → **`td_mebli_cutting`** → **`td_mebli_dashboard`** → **`td_mebli_demo`**. Нові (повний обсяг): `td_mebli_measure` (S-15; `crm, sale`), `td_mebli_shop` (S-06 кіоск за PIN, точки якості з фото, S-16; `mrp, hr, stock`), `td_mebli_purchase` (S-08 ціна ↔ історія; `purchase_stock`), `td_mebli_install` (S-12, S-17 нарахування; `project`), `td_mebli_claim` (S-14; `repair`), `td_mebli_cost` (S-11; адаптований REUSE-01; `sale_mrp, project_mrp_account`), `td_mebli_bas` (статус обміну — імітація). EE — `td_mebli_*_ee` (`auto_install`) лише після доступу до EE.
Усі модулі: версія `19.0.1.0.0`, ліцензія LGPL-3 (за замовчуванням; остаточно — рішення власника, №14 відкрите), AGPL-залежностей немає, OCA — лише ідеї. Рядки коду й подань англійською, переклад у `i18n/uk.po`.

**Зразок змінює:**
- `td_mebli_sale` — `depends` + `sale_purchase_stock`, `purchase_mrp` (CE, `auto_install`-ланки стандарту); **моделі `td.mebli.order.item` немає** (видалено разом із правами); лише compute-поля (не збережені, лише читання): `sale.order.td_purchase_line_ids`, `td_shop_date`, `td_forecast_date`, `td_delay_days`, `td_late_line_id`, `td_late_item`, `td_delay_reason`; `purchase.order.line.td_date_ready`; подання: банер «дата під загрозою», блок дат у формі, вкладка «Закупівлі під замовлення» (рядки стандартних замовлень на купівлю, `readonly`, без створення/видалення; група `purchase.group_purchase_user`), колонки в списку; переклад `i18n/uk.po`; тести `tests/test_order_dates.py`.
- `td_mebli_mrp` — специфікація замовлення копіює стандартні `produce_delay` і `days_to_prepare_mo` шаблону (раніше 0 → кінець МО «місяці»).
- `td_mebli_demo` — `dates.py`: вигадані постачальники; замовні позиції як стандартні товари (MTO + «Купити», `product.supplierinfo` з постачальником і строком), рядки специфікацій-шаблонів кухні й шафи-купе, `produce_delay` 12 дн. шаблонів; замовлення показу «кухня + шафа-купе» підтверджується — стандарт створює МО і 3 закупівлі; комірник у модулі Закупівлі підтверджує їх, вводить перенесену фарбоцехом дату (`date_planned`) і приймає профіль купе; `showcase.py` — менеджеру салону й комірнику група «Закупівлі: користувач».

**Вимога до модуля дашборда:** корінь екрана — `td_dash_grid`, картка — `td_card` (переписування `td_mebli_dashboard` під KPI BOX §11.1 — повний обсяг).

## 4. Продаючі вимоги (обов'язково)
- Історія «біль → вигода» на кожен крок: зразок — PAIN-16 (ROLE-02, «обіцяли два місяці, вийшло три») → банер і червона прогнозна дата **до** зриву, причина «постачальник» і позиція, що зсуває.
- Брендинг демо-клієнта: «Меблева фабрика «Демо»» з логотипом (вигадана, `OWNER-INTAKE.brand.demo_client: вигаданий`); ролі-користувачі з логінами `<роль>@demo-fabryka.example` і аватарами (менеджер салону, технолог, начальник виробництва, комірник, фінансист, власник).
- Калібровані дані: маржа замовлень з розкидом і нижчими за поріг (замовлення показу з урахуванням закуплених позицій — близько 20 %); замовлення показу має 3 закупівлі: фасади — пізно, стільниця — вчасно, профіль купе — отримано; у книзі замовлень одне відкрите замовлення із зсувом через цех («Компанія»). Закупівель у старих замовленнях книги немає (вони підтверджені до появи закуплених позицій у специфікаціях-шаблонах).
- Видимий ефект у кадрі: дні зсуву, прогнозна дата, закупівля й постачальник, смарт-кнопка «Купівлі»; без «Новий», без порожніх обов'язкових полів, без англійських підписів, текст не обрізаний.
- Чесні позначки імітацій (§5) — компактно, на екрані й у README.

## 5. Імітації
- У зразку імітацій немає: закупівлі, дати постачальника й отримання — справжні стандартні документи модуля Закупівлі.
- Повний обсяг: статус обміну з BAS (F-47), курс НБУ без мережі (F-26), розпізнавання колонок CAD-файлу (F-27, на CSV) — позначка «імітація» на екрані й у README.

## 6. Сценарії зйомки
| Крок SALES §6 | Екран | Роль | PAIN-xx | Рядок SALES §2 | Що видно (ефект) | Мобільний |
|---|---|---|---|---|---|---|
| **0 (зразок) — сцена 4 «Замовні фасади затримуються»** | S-02 | ROLE-02 менеджер салону (`salon`) | PAIN-16 | 5 «Нам вистачає Excel і Viber» | обіцяна 4 груд.<!--fact:facts.00-sample.promised_date--> і прогнозна 18 груд.<!--fact:facts.00-sample.forecast_date--> дата, зсув на 14<!--fact:facts.00-sample.delay_days--> днів, причина «Постачальник», закупівля «Фасади МДФ фарбовані…» від «Фарбоцех «Палітра»», дата постачальника в закупівлі 6 груд.<!--fact:facts.00-sample.late_item_supplier_date-->, готовність за позицією 18 груд.<!--fact:facts.00-sample.late_item_ready-->, закупівля P00001<!--fact:facts.00-sample.late_purchase-->; менеджер салону — лише читання закупівель свого замовлення (без групи «Закупівлі», смарт-кнопки немає); планова маржа 20,02%<!--fact:facts.D_sample.margin_percent--> | ні (повний обсяг — так) |
| 1–8 (повний обсяг) | S-15 … S-19 за §1 | ROLE-09, 02, 01, 03, 05, 10, 06, 08 | за `concept/scenarios.md` SC-01…SC-08 | 1–13 | за §1 | ≥4 кроки ролей: замір, планшет цеху, акт монтажу, дашборд |

Прохід 1 (змінює дані) — у зразку порожній; прохід 2 (лише читання) — крок 0 і кліп `D_sample`. Сцени `facts.json`: `00-sample` (скриншот-крок), `D_sample` (кліп).

## 7. Складність і ризики
`complexity.md` — повний обсяг (Крок 8). Відомі ризики й дефекти для **беклогу A-11**:
- Перерахунок `_compute_date_finished` (`mrp_production.py:786-795`) при `produce_delay = 0` зсуває кінець МО за вільністю дільниць — виправлено в зразку: специфікація замовлення копіює `produce_delay` шаблону; у шаблонах кухні й шафи-купе демо — 12 дн., решта шаблонів — 0 (заповнити в повному обсязі).
- Закрито (рецензія Архітектора, коло 1): `mrp.workcenter.td_capacity_hours` — compute з календаря дільниці (`hours_per_week` × паралельність), у демо дільниці отримують стандартні календарі `resource.calendar`; відкриті години — `workcenter_load`.
- Готовність за закупленою позицією = дата поставки + `produce_delay` усієї специфікації (стандартне припущення планування МО: компоненти потрібні на старті). Для фасадів, що монтуються наприкінці, це песимістично; точніше — від операції, у якій компонент споживається (`mrp.bom.line.operation_id`, стандарт), — уточнення для повного обсягу, нових полів не потребує.
- Старі замовлення книги не мають закупівель (підтверджені до додавання закуплених компонентів у шаблони) — для дошки S-05 у повному обсязі seed треба підтверджувати замовлення після налаштування шаблонів.
- Заголовок колонки «Одиниця» у рядках замовлення стандартного подання обрізано до «Один» (ширина колонки `sale.view_order_form`) — правка ширини в A-11.
- Попередження Odoo «Access Rights Inconsistency» (поле `margin_percent`) у списках `td_mebli_sale/views/order_cost_report_views.xml` — з попереднього зрізу, не зразка.

## 8. Відкриті питання до людини
1. Чи приймаєте зразок (екран S-02 «дата під загрозою» і запис 15 с) як напрям для повного обсягу? Стиль кадру, роль у кадрі, швидкість.
2. Чи перший екран демо — саме S-02 (варіант цінності 1), а дашборд S-19 — у кінці показу (сцена 8), як у SALES §6?
3. Перевірка №13: два пункти CE не підтвердились (кіоск цеху за PIN, курс НБУ) — лишаємо `td_` з верхньою межею годин чи переносимо в «умовно»? EE-частина — хто й коли дасть доступ до чистої бази EE?
4. Закрито рецензією Архітектора (коло 1): менеджер салону без групи «Закупівлі»; `td_mebli_sale` дає продавцю лише читання `purchase.order`/`purchase.order.line` своїх замовлень (правило за `reference_ids.sale_ids.user_id`), вкладку бачить, смарт-кнопка — лише закупівельникам (стандарт). Залишається: чи має менеджер з «Усі документи» (`group_sale_salesman_all_leads`) читати закупівлі всіх замовлень (так зроблено зараз)?
