# План зрізу A-21 (спроба 2) — пакет «меблі» на базі Odoo 19 CE

Дата: 2026-11-12 · гілка `flow/A-21-2-test` · автор: AI (prototype-builder 0.2.1; переробка зразка за 0.2.1 — зворотна перевірка стандарту, §23) · **статус: повний обсяг, хвиля 1 з 3 (модулі й демо-дані; зразок прийнято — `flow/decisions.md` запис 36)** ·
`demo_edition: ce` (OWNER-INTAKE) · SHA входів: `413e82a` (OWNER-INTAKE, `concept/*`, `research/*`) · `ODOO_HOME` = `/home/user/odoo19/src` @ `40e9be2b5ab8828bdab450fb6c8c40f2104a36a6` (19.0, 2026-11-10).
Мета: справжні модулі `package/addons/td_mebli_*` (Python + XML + дані), без Studio й полів `x_`, на чистій базі Odoo 19 CE; EE — лише окремою позначкою (`td_mebli_*_ee` з `auto_install`), без EE-залежностей ядра.
Вхід (К-05): `research/FUNCTIONAL-MAP.md` §4.5–4.6, `research/BOX.md` §1, §11.1, §12–13, `research/SALES.md` §2, §4, §6, `research/REUSE.md`, `concept/{features,screens,scenarios}.md` (v2), рішення власника `flow/decisions.md` 23, 30, 31, 35. Попередній зріз (`prototype-real/` і 5 модулів `td_mebli_*` від A-21-real) — **матеріал, не вхід**: код перевикористовується, екрани беруться з концепції v2.
Режим наряду: `params.mode: recalc`. Зроблено: Крок 1–2 (зразок, прийнято, запис 36). **Хвиля 1 повного обсягу (цей запуск):** Кроки 3–5 — модулі під усі сцени SALES §6, демо-дані, база `demo-mebli-full`, тести; кроки й кліпи зйомки підготовлено, не знято. Хвиля 2 — запис десктопа; хвиля 3 — мобільний запис, `facts.json`, `complexity.md`, README.
**Замовчування запису 36:** порядок демо — за SALES §6 (S-02 першим, дашборд S-19 у кінці); кіоск цеху за PIN і курс НБУ — свої `td_` з верхньою межею годин (стандарт CE їх не має — «Перевірка №13»); права продавця на закупівлі — як у зразку. Склад коробки A — рішення №16 (запис 31).
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

**Повний обсяг (хвиля 1): сцена → екран → роль → що в Odoo → основа.** Порядок показу — SALES §6 (запис 36): сцена 4 / S-02 першою (прийнятий зразок), далі 1 → 1а → 2 → 3 → 5 → 5а → 6 → 7, дашборд S-19 — у кінці.

| # | Сцена SALES §6 | Екран (меню) | Роль (логін демо) | Кроки в кадрі | Стд CE | `td_` (модуль) | Інтегр / імітація |
|---|---|---|---|---|---|---|---|
| 4 | Замовні фасади затримуються | S-02 Замовлення S00123; S-08 закупівлі | менеджер салону (`salon`) | банер «прогнозна пізніша на N днів», вкладка «Закупівлі під замовлення», причина «Постачальник» | MTO + «Купити», `purchase.order.line.date_planned`, смарт-кнопка `sale_purchase` | `td_mebli_sale` (лише compute) | — |
| 1 | Замір із помилкою | S-15 «Замір-листи» (Продажі) → ЗМ замовлення S00123 | замірник (`measure`) | ніші й техніка; «Холодильник: глибше на 30 мм» червоним; «Звірити з проєктом» | CRM-нагода (`sale_crm`), зустріч — календар | `td_mebli_measure` (`td.mebli.measure`, ніші, техніка) | — |
| 1а | Підбір виробу й ціна з розмірів | S-01 → S-02 рядок | менеджер салону | конфігуратор, ціна з розмірів у рядку | атрибути товару, `sale_margin` | `td_mebli_sale` (є зі зрізу) | — |
| 2 | Пропозиція й погодження | S-03 специфікація → «Імпорт деталей» (CSV) → S-02 маржа, графік оплат, підпис порталом | технолог (`tech`), менеджер | розпізнавання колонок CSV, деталі в специфікації; маржа до підтвердження; умови оплати «Передоплата 50%» | `account.payment.term` (графік оплат), підпис пропозиції порталом | `td_mebli_mrp` (`td.mebli.spec.import`) | формати CAD-програм — лише CSV-вивантаження (імітації читання CAD немає) |
| 3 | Зміна фасадів (B) | S-02 вкладка «Зміни», кнопки «Створити зміну» / «Зафіксувати зміну» | менеджер салону | версія 2, причина «Клієнт», ціна +, обіцяна дата +7 дн. | `commitment_date`, рядки замовлення (ввід — у стандарті) | `td_mebli_sale` (`td.mebli.order.change`: причина + знімки «до/після») | підпис версії клієнтом — B, не в зрізі |
| 5 | Цех і комплектація | S-06 «Планшет цеху» (Виробництво); S-16 «Комплектувальні листи» (Склад) | планшет (`tablet`) + PIN працівника; комірник (`store`) | «Взято / Пауза з причиною / Зроблено» з PIN; «Підтвердити» відвантаження → «Комплект неповний: бракує … (місце N)» | робочі замовлення, таймер і причини простою `mrp.workcenter.productivity(.loss)`, відвантаження `stock.picking` | `td_mebli_shop` (кіоск, лист, блок відвантаження) | — |
| 5а | Розкрій пакетом, обрізки, якість (B) | S-04 «Розкрій»; S-06 «Якість» з фото | технолог; оператор кромкування | пакет за декором, ділові обрізки; крок якості з фото до «Зроблено» | партії `stock.lot` | `td_mebli_cutting` (є), `td_mebli_shop` (`td.mebli.quality.check`) | оптимізатор розкрою **не показуємо** (OUT-02) |
| 6 | Монтаж і акт | S-12 «Календар монтажів» (Проєкт) → задача → «Акти» | бригадир (`fitter`), телефон | два виїзди S00123 (корпуси → стільниця); акт з недоліком, фото, підпис пальцем; % бригаді | задачі `project` з рядка-послуги `sale_project`, календар (без Ганта) | `td_mebli_install` (`td.mebli.install.act`, недоліки) | — |
| 6/8 | Нарахування | S-17 «Нарахування» (Виробництво › Звітність) | фінансист (`fin`) | «Нарахувати»: відрядна з часу планшета × ставка, % бригаді з акта, премія/штраф з причиною | `hr_hourly_cost.hourly_cost`, час робіт | `td_mebli_install` (`td.mebli.accrual`) | передача в BAS — імітація статусу |
| 7 | Рекламація і план ↔ факт | S-14 «Рекламації» (Ремонт); S-11 «Собівартість: план і факт» (Продажі › Звітність) | начальник виробництва (`chief`), фінансист | канбан рекламацій, «Прострочено», причина й хто платить; план ↔ факт по замовленнях | `repair.order`, `sale_margin`, дані МО (як «Огляд МО») | `td_mebli_claim`, `td_mebli_cost` | — |
| 8 | Дашборд керівника | S-19 «Дашборд керівника» | власник (`owner`) | 11 карток BOX §11.1 (KPI 1–10 + ціни постачальників); картка → записи, які вона порахувала | — | `td_mebli_dashboard`, `td_mebli_purchase` (ціни ↔ історія) | рядок «невідповідності якості» — B/C, не показується |
| — | Курс НБУ, обмін з BAS | валюти; S-02 поле «Обмін з BAS» | фінансист | курси в стандартних `res.currency.rate` з позначкою джерела | `res.currency.rate` | `td_mebli_ua` | **імітація:** курси демо без мережі (`td_source = nbu_imitation`), статус BAS ставить кнопка «Передати в BAS (імітація)» |

**Кіоск за PIN і курс НБУ — `td_` з верхньою межею годин (запис 36, «Перевірка №13»):** кіоск — спільний користувач-планшет + PIN стандартного `hr.employee` (зразок перевірки PIN — `hr_attendance/controllers/main.py:203-208`), без окремого публічного контролера; курс НБУ — завантаження в стандартну таблицю курсів, онлайн вимкнено параметром `td_mebli_ua.nbu_online`. Межі годин для A-08 — у `complexity.md` (хвиля 3).

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

**Повний обсяг, хвиля 1 (нові `td_`-моделі й поля).** Ввід стандартних даних у `td_` заборонено (0.2.1): усе, що веде стандартний модуль (закупівля, склад, виробництво, рахунки, задачі, ремонти, курси), вводиться там; `td_` — сутності без аналога або compute/related. Шляхи — від `ODOO_HOME/addons/` (19.0 CE @ `40e9be2b`).

| Модель / поле | Нова чи розширення (`_inherit`) | Стандартний аналог (файл:рядок 19.0) | Чому не стандарт |
|---|---|---|---|
| `td.mebli.measure` | нова (S-15) | нагода й зустріч — `crm/models/crm_lead.py:85`, `sale_crm/models/sale_order.py:10` (`opportunity_id`); вкладення — `mail` | замір-лист (ніші, кути, комунікації) — у CRM полів немає; нагода й зустріч лишаються стандартними |
| `td.mebli.measure.niche` | нова | немає | розміри ніші об'єкта клієнта — сутність без аналога |
| `td.mebli.measure.appliance` | нова | немає | техніка клієнта з розмірами й перевіркою «вміщається» — без аналога |
| `sale.order.td_measure_ids` | розширення, обернений зв'язок (One2many) | — | показ замір-листів замовлення |
| `sale.order.td_measure_count` | розширення, compute | — | лічильник смарт-кнопки |
| `crm.lead.td_measure_ids` | розширення, обернений зв'язок | — | замір-листи нагоди |
| `mrp.workcenter.productivity.td_employee_id` | розширення, ставить система (кіоск) | `mrp/models/mrp_workcenter.py:531` (`user_id` — лише користувач Odoo) | у CE час пишеться на користувача; працівник цеху без користувача (PIN `hr/models/hr_employee.py:211`) — «Перевірка №13», кіоск не підтверджено |
| `mrp.routing.workcenter.td_quality_point` | розширення, ввід | `quality_control` — лише EE (`odoo/addons/base/data/ir_module_module.xml:131`) | крок якості операції в CE відсутній |
| `mrp.workorder.td_quality_point` | розширення, related | `operation_id` (`mrp/models/mrp_workorder.py:102`) | — |
| `mrp.workorder.td_quality_ids` | розширення, обернений зв'язок | — | перевірки якості робочого замовлення |
| `mrp.workorder.td_quality_state` | розширення, compute | — | стан кроку якості з перевірок |
| `mrp.workorder.td_worker_names` | розширення, compute | `time_ids` (`mrp/models/mrp_workorder.py:118`) | — |
| `mrp.workorder.td_pause_reason` | розширення, compute | `loss_id` відкритого рядка часу (`mrp/models/mrp_workcenter.py:534`) | — |
| `td.mebli.quality.check` | нова | `quality_control` — лише EE (`odoo/addons/base/data/ir_module_module.xml:131`) | перевірка з фото й результатом на CE |
| `td.mebli.kiosk` | нова (TransientModel) | кіоск відвідувань `hr_attendance/controllers/main.py:139`, `:203-208` — лише відвідування | діалог PIN планшета; час — стандартні `button_start`/`button_pending`/`button_finish` (`mrp/models/mrp_workorder.py:667`, `:764`, `:716`) |
| `td.mebli.kit.line` | нова (S-16) | пакунки `stock/models/stock_package.py:18` — на товари складу, не на деталі | деталі розкрою не є товарами складу; місце й «зібрано» по деталі — без аналога |
| `sale.order.td_kit_line_ids` | розширення, обернений зв'язок | — | лист комплектації замовлення |
| `sale.order.td_kit_missing` | розширення, compute | — | лічильник незібраного |
| `sale.order.td_kit_places` | розширення, compute | — | кількість місць |
| `td.mebli.install.act` | нова (S-12) | задача-виїзд `project/models/project_task.py:183` (`date_deadline`), `sale_project/models/project_task.py:25` (`sale_order_id`); підпис — віджет `web/static/src/views/fields/signature/signature_field.js:14` | акт етапу/фінальний з чек-листом, підписом клієнта, % бригаді — у CE немає (Field Service — EE) |
| `td.mebli.install.defect` | нова | немає | недолік акта з фото |
| `project.task.td_act_ids` | розширення, обернений зв'язок | — | акти виїзду |
| `project.task.td_act_count` | розширення, compute | — | смарт-кнопка |
| `td.mebli.accrual` | нова (S-17) | Payroll — лише EE і без України (FM §4.5); ставка — `hr_hourly_cost/models/hr_employee.py:9` (`hourly_cost`), години — `mrp/models/mrp_workcenter.py:542` (`duration`) | нарахування відрядної, % бригаді, премій і штрафів з причиною для передачі в облік клієнта |
| `repair.order.td_claim_order_id` | розширення, ввід | `repair/models/repair.py:168` (`sale_order_id` — замовлення, з якого продано ремонт, інший зміст) | замовлення меблів, на яке скарга |
| `repair.order.td_part_id` | розширення, ввід | немає | деталь специфікації замовлення |
| `repair.order.td_reason` | розширення, ввід | немає | причина рекламації |
| `repair.order.td_payer` | розширення, ввід | немає | хто платить |
| `repair.order.td_photo` | розширення, ввід | вкладення чату (`mail`) | фото в картці канбана |
| `repair.order.td_remake_production_id` | розширення, ставить система | `mrp.production` створюється стандартом (`origin` = рекламація) | посилання на повторне виготовлення |
| `repair.order.td_days_open` | розширення, compute | `repair/models/repair.py:67` (`schedule_date`), `create_date` | — |
| `repair.order.td_overdue` | розширення, compute | `repair/models/repair.py:67` | — |
| `sale.order.td_claim_ids` | розширення, обернений зв'язок | — | рекламації замовлення |
| `sale.order.td_claim_count` | розширення, compute | — | смарт-кнопка |
| `sale.order.td_cost_plan` | розширення, compute | `sale_margin/models/sale_order.py:10` (`margin`): план = виручка − маржа | — |
| `sale.order.td_cost_material` | розширення, compute | як `mrp/report/mrp_report_mo_overview.py:227` (спожите × `standard_price`) | — |
| `sale.order.td_cost_work` | розширення, compute | як `mrp/report/mrp_report_mo_overview.py:385` (години × `costs_hour`) | — |
| `sale.order.td_cost_fact` | розширення, compute | сума двох рядків вище | — |
| `sale.order.td_margin_fact` | розширення, compute | — | — (похідна) |
| `sale.order.td_margin_fact_pct` | розширення, compute | — | — (похідна) |
| `sale.order.td_margin_plan_pct` | розширення, compute | `sale_margin/models/sale_order.py:11` (`margin_percent`) | — (та сама зважена формула) |
| `sale.order.td_cost_deviation_pct` | розширення, compute | — | — (похідна) |
| `sale.order.td_cost_has_fact` | розширення, compute | стан МО `mrp/models/mrp_production.py:177` | — |
| `purchase.order.line.td_history_price` | розширення, compute (збережене для фільтра) | `purchase/models/purchase_order_line.py:46` (`price_unit` попередніх закупівель, читаємо) | — |
| `purchase.order.line.td_price_delta_pct` | розширення, compute | те саме | — |
| `purchase.order.line.td_overpay` | розширення, compute | те саме | — |
| `purchase.order.line.td_over_history` | розширення, compute | те саме | — |
| `res.currency.rate.td_source` | розширення, ставить система | `odoo/addons/base/models/res_currency.py:353-355` (дата й курс — стандарт; джерела немає) | позначка «НБУ / імітація» |
| `sale.order.td_bas_state` | розширення, ставить система (імітація) | немає (обміну з BAS у CE немає) | статус обміну H-12 |
| `td.mebli.order.change` | нова (S-18) | трекінг змін `mail` (`commitment_date`, сума) — без причини й версії | версія зміни з причиною «Клієнт/Компанія/Постачальник»; ціна й дата «до/після» — знімки стандартних полів, ставить система, не ввід |
| `td.mebli.order.change.wizard` | нова (TransientModel) | — | діалог «Створити зміну» |
| `sale.order.td_change_ids` | розширення, обернений зв'язок | — | вкладка «Зміни» |
| `sale.order.td_change_open` | розширення, compute | — | кнопки |
| `td.mebli.spec.import` | нова (TransientModel) | стандартний імпорт CSV `base_import` — без розпізнавання назв колонок CAD-вивантажень і без деталей | розпізнавання колонок за синонімами заголовків → `td.mebli.part` |
| `sale.order.td_dash_paid` | розширення, compute | `account/models/account_move.py:565` (`amount_residual` рахунків) | — |
| `sale.order.td_dash_due` | розширення, compute | `amount_total` − оплачене | — |

## 3. Модулі

Граф (стрілка — `depends`; лише CE): `mrp_account, stock` → **`td_mebli_mrp`** → **`td_mebli_sale`** (`+ sale_mrp, sale_margin`) → **`td_mebli_cutting`** → **`td_mebli_dashboard`** → **`td_mebli_demo`**. Нові (повний обсяг): `td_mebli_measure` (S-15; `crm, sale`), `td_mebli_shop` (S-06 кіоск за PIN, точки якості з фото, S-16; `mrp, hr, stock`), `td_mebli_purchase` (S-08 ціна ↔ історія; `purchase_stock`), `td_mebli_install` (S-12, S-17 нарахування; `project`), `td_mebli_claim` (S-14; `repair`), `td_mebli_cost` (S-11; адаптований REUSE-01; `sale_mrp, project_mrp_account`), `td_mebli_bas` (статус обміну — імітація). EE — `td_mebli_*_ee` (`auto_install`) лише після доступу до EE.
Усі модулі: версія `19.0.1.0.0`, ліцензія LGPL-3 (за замовчуванням; остаточно — рішення власника, №14 відкрите), AGPL-залежностей немає, OCA — лише ідеї. Рядки коду й подань англійською, переклад у `i18n/uk.po`.

**Повний обсяг, хвиля 1 — фактичний граф (лише CE, без EE/AGPL-залежностей):**
`td_mebli_mrp` (+ `td.mebli.spec.import`, S-03) → `td_mebli_sale` (+ `td.mebli.order.change`, S-18) → `td_mebli_cutting` (S-04);
`td_mebli_sale` + `sale_crm` → **`td_mebli_measure`** (S-15); `td_mebli_sale` + `hr_hourly_cost`, `sale_stock` → **`td_mebli_shop`** (S-06 кіоск, якість; S-16 лист і блок відвантаження) → **`td_mebli_install`** (+ `sale_project`; S-12 акти, S-17 нарахування);
`td_mebli_sale` + `repair` → **`td_mebli_claim`** (S-14); `td_mebli_sale` → **`td_mebli_cost`** (S-11, ідея REUSE-01 без копіювання коду: репо REUSE-01 у сесії не читалось); `purchase_stock` → **`td_mebli_purchase`** (S-08 ціни ↔ історія); `sale` → **`td_mebli_ua`** (F-26 курс НБУ, F-47 статус BAS);
усі → **`td_mebli_dashboard`** (S-19, переписано: 11 карток BOX §11.1, корінь `.td_dash_grid`, картка `.td_card`, кожна картка відкриває рівно ті записи, які порахувала; одна зважена маржа) → **`td_mebli_demo`**.
Окремого `td_mebli_bas` і `td_mebli_*_ee` немає (EE недоступна — «не перевірено»). Плитку завантаження виправлено (відкладений minor Архітектора): відкрита робота з плановим стартом до +7 днів ÷ тижневих годин календаря дільниці (не вся черга); вся черга — окремим рядком «Відкрита черга, тижнів роботи».

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
- Зразок (S-02): імітацій немає — закупівлі, дати постачальника й отримання — стандартні документи Закупівель.
- **Курс НБУ (F-26):** код завантаження в стандартні `res.currency.rate` справжній, онлайн вимкнено (`td_mebli_ua.nbu_online`); у демо курси EUR/USD записано з таблиці демо (не реальні) з позначкою джерела «НБУ (імітація, без мережі)». Причина: мережі до НБУ в середовищі зрізу немає, а реальні курси в кадрі — дані з пам'яті.
- **Обмін з BAS (F-47):** лише статус на замовленні й кнопка «Передати в BAS (імітація)»; самого обміну немає (інтеграція H-12, окремий проєкт).
- **Файли CAD (F-27):** справжній імпорт CSV-вивантаження з розпізнаванням колонок за заголовками; читання форматів самих програм — не в зрізі (позначено в діалозі).
- **Підпис і фото на телефоні:** стандартний віджет підпису й завантаження файлу; камера й підпис пальцем на реальному пристрої — не перевірено (немає пристрою).
- **Оптимізатор розкрою** — не показується (OUT-02); код попереднього зрізу лишився в `td_mebli_cutting`, у сценах не відкривається.

## 6. Сценарії зйомки
| Крок SALES §6 | Екран | Роль | PAIN-xx | Рядок SALES §2 | Що видно (ефект) | Мобільний |
|---|---|---|---|---|---|---|
| **0 (зразок) — сцена 4 «Замовні фасади затримуються»** | S-02 | ROLE-02 менеджер салону (`salon`) | PAIN-16 | 5 «Нам вистачає Excel і Viber» | обіцяна 4 груд.<!--fact:facts.00-sample.promised_date--> і прогнозна 18 груд.<!--fact:facts.00-sample.forecast_date--> дата, зсув на 14<!--fact:facts.00-sample.delay_days--> днів, причина «Постачальник», закупівля «Фасади МДФ фарбовані…» від «Фарбоцех «Палітра»», дата постачальника в закупівлі 6 груд.<!--fact:facts.00-sample.late_item_supplier_date-->, готовність за позицією 18 груд.<!--fact:facts.00-sample.late_item_ready-->, закупівля P00001<!--fact:facts.00-sample.late_purchase-->; менеджер салону — лише читання закупівель свого замовлення (без групи «Закупівлі», смарт-кнопки немає); планова маржа 20,02%<!--fact:facts.D_sample.margin_percent--> | ні (повний обсяг — так) |
| 1 Замір | S-15 | ROLE-09 замірник (`measure`) | IM:S23 «холодильник виступає» | 1 | «Холодильник: глибше на 30 мм» до виробництва | m1 |
| 1а Ціна з розмірів | S-01 → S-02 | ROLE-02 (`salon`) | ручний прорахунок | — | ціна з розмірів у рядку, маржа | — |
| 2 Пропозиція | S-03 імпорт CSV, S-02 | ROLE-01 технолог (`tech`) | ручне перенесення деталей | — | колонки розпізнано, деталі в специфікації | — |
| 3 Зміна фасадів (B) | S-02 «Зміни» | ROLE-02 | договір | — | версія 2, причина «Клієнт», ціна й дата | — |
| 5 Цех і комплектація | S-06, S-16 | планшет + PIN; ROLE-05 комірник (`store`) | контроль комплектації | — | «Взято» за PIN; «Не запаковано: задня стінка» | m2 |
| 5а Розкрій і якість (B) | S-04, S-06 | ROLE-01 | обрізки, пакет | — | пакет за декором, обрізки, крок якості з фото | — |
| 6 Монтаж і акт | S-12, S-17 | ROLE-10 бригадир (`fitter`), ROLE-06 (`fin`) | «монтаж тягнеться тижнями»; % бригаді в Excel | — | два виїзди S00123; акт з недоліком; % бригаді; премії й штрафи | m3 |
| 7 Рекламація, план ↔ факт | S-14, S-11 | ROLE-03 (`chief`), ROLE-06 | «рекламацію не виконували 4 місяці» | — | канбан, «Прострочено»; план ↔ факт | — |
| 8 Дашборд | S-19 (+ S-08 ціни) | ROLE-08 власник (`owner`) | KPI перелік IM §3.2 | — | 11 карток, картка = drill-down | m5 (+ m4 S-02) |

Файли кроків (хвиля 1 підготувала, не знято): `shoot/scenario.steps.mjs` (кроки 0–16; PASS1 = 3, 5 — імпорт CSV і «Взято» з PIN; PASS2 — решта, дашборд останнім), `shoot/scenario-mobile.steps.mjs` (5 кроків ролей m1–m5), `shoot/clips.mjs` (11 кліпів; PASS1 = D_csv, D_tablet, D_kit), `shoot/data/kitchen-spec.csv` (вигаданий CSV для сцени 2). Селектори звіряє хвиля 2 на живій базі.

**База показу `demo-mebli-full` (Крок 5; C-00 `tools/odoo/` у репо немає — прямі команди, рівнозначні `build_db.sh`):**
```
dropdb --if-exists demo-mebli-full
$ODOO_PY $ODOO_BIN -c $ODOO_CONF -d demo-mebli-full -i td_mebli_demo --load-language uk_UA --without-demo=True --stop-after-init
$ODOO_PY $ODOO_BIN -c $ODOO_CONF -d demo-mebli-full -u td_mebli_mrp,td_mebli_sale,td_mebli_cutting,td_mebli_measure,td_mebli_shop,td_mebli_install,td_mebli_claim,td_mebli_cost,td_mebli_purchase,td_mebli_ua,td_mebli_dashboard,td_mebli_demo --load-language uk_UA --i18n-overwrite --stop-after-init
$ODOO_PY $ODOO_BIN shell -c $ODOO_CONF -d demo-mebli-full < package/addons/td_mebli_demo/scripts/seed_showcase.py   # seed_showcase -> seed_dates -> seed_full, commit
psql -d demo-mebli-full -c "SELECT count(*) FROM td_mebli_install_act"   # > 0, інакше seed не закомічено (--check-table td_mebli_install_act)
```

Прохід 1 (змінює дані) — у зразку порожній; прохід 2 (лише читання) — крок 0 і кліп `D_sample`. Сцени `facts.json`: `00-sample` (скриншот-крок), `D_sample` (кліп).

## 7. Складність і ризики
`complexity.md` — повний обсяг (Крок 8). Відомі ризики й дефекти для **беклогу A-11**:
- Перерахунок `_compute_date_finished` (`mrp_production.py:786-795`) при `produce_delay = 0` зсуває кінець МО за вільністю дільниць — виправлено в зразку: специфікація замовлення копіює `produce_delay` шаблону; у шаблонах кухні й шафи-купе демо — 12 дн., решта шаблонів — 0 (заповнити в повному обсязі).
- Закрито (рецензія Архітектора, коло 1): `mrp.workcenter.td_capacity_hours` — compute з календаря дільниці (`hours_per_week` × паралельність), у демо дільниці отримують стандартні календарі `resource.calendar`; відкриті години — `workcenter_load`.
- Готовність за закупленою позицією = дата поставки + `produce_delay` усієї специфікації (стандартне припущення планування МО: компоненти потрібні на старті). Для фасадів, що монтуються наприкінці, це песимістично; точніше — від операції, у якій компонент споживається (`mrp.bom.line.operation_id`, стандарт), — уточнення для повного обсягу, нових полів не потребує.
- Старі замовлення книги не мають закупівель (підтверджені до додавання закуплених компонентів у шаблони) — для дошки S-05 у повному обсязі seed треба підтверджувати замовлення після налаштування шаблонів.
- Заголовок колонки «Одиниця» у рядках замовлення стандартного подання обрізано до «Один» (ширина колонки `sale.view_order_form`) — правка ширини в A-11.
- Попередження Odoo «Access Rights Inconsistency» (поле `margin_percent`) у списках `td_mebli_sale/views/order_cost_report_views.xml` — з попереднього зрізу, не зразка.

- **Прийнятий екран S-02 (N-11, було / стало):** було — шапка форми зі стандартними кнопками; стало — додано кнопки «Створити зміну» (сцена 3) і «Передати в BAS (імітація)», поле «Обмін з BAS» біля умов оплати, смарт-кнопки «Заміри», «Не запаковано»; банер, блок дат і вкладка «Закупівлі під замовлення» не змінювались. Перезйомку `D_sample` у хвилі 2 — лише після згоди людини (або сховати нові кнопки для ролі в кадрі).
- **Хвиля 1 (нове):** демо-дані: відрядна = години рядків часу планшета × стандартна погодинна ставка працівника (`hourly_cost`), а не розцінка за операцію — уточнити методику з галуззю (A-06); кіоск — спільний користувач-планшет і PIN, без публічного маршруту (безпечніше, але потрібна сесія планшета); у CE таймер робочого замовлення один на користувача — двоє працівників на одному замовленні через один планшет одночасно не працюють (межа `td_` кіоску, години A-08); «Застряглі» — без руху понад 5 днів (параметр у коді, у A-11 — налаштування); фото в демо — зображення товарів-заглушки.

## 8. Відкриті питання до людини
**Хвиля 1:** питання 1–4 закрито записом 36 (зразок прийнято, порядок — SALES §6, кіоск і курс НБУ — `td_` з межею годин, права — як у зразку). Нові:
5. Відрядна в демо рахується як години × погодинна ставка працівника; чи потрібна розцінка за операцію (грн за деталь / м кромки) — це нове поле на операції (`td_`)?
6. Монтаж «у вартості замовлення» (рядок-послуга 0 грн створює задачу виїзду стандартом `sale_project`) — чи так продає фабрика, чи монтаж — окрема платна позиція?

Попередні (зразок):
1. Чи приймаєте зразок (екран S-02 «дата під загрозою» і запис 15 с) як напрям для повного обсягу? Стиль кадру, роль у кадрі, швидкість.
2. Чи перший екран демо — саме S-02 (варіант цінності 1), а дашборд S-19 — у кінці показу (сцена 8), як у SALES §6?
3. Перевірка №13: два пункти CE не підтвердились (кіоск цеху за PIN, курс НБУ) — лишаємо `td_` з верхньою межею годин чи переносимо в «умовно»? EE-частина — хто й коли дасть доступ до чистої бази EE?
4. Закрито рецензією Архітектора (коло 1): менеджер салону без групи «Закупівлі»; `td_mebli_sale` дає продавцю лише читання `purchase.order`/`purchase.order.line` своїх замовлень (правило за `reference_ids.sale_ids.user_id`), вкладку бачить, смарт-кнопка — лише закупівельникам (стандарт). Залишається: чи має менеджер з «Усі документи» (`group_sale_salesman_all_leads`) читати закупівлі всіх замовлень (так зроблено зараз)?
