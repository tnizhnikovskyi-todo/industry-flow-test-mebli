# План еталонного зрізу «меблі» в Odoo 19 CE (A-21-real, заготовка A-11)

Дата: 2026-11-10. Гілка `flow/A-21-real`. Автор: Архітектор рішення (AI). Статус: чернетка, рішення приймає людина.
Вихідники Odoo: `ODOO_HOME=/home/user/odoo19` (19.0, коміт `ab862495`, 2026-11-10). Усі посилання `файл:рядок` нижче — відносно `$ODOO_HOME/addons`.
Мета: справжні модулі `td_mebli_*` (Python + XML + дані), без Studio і без `x_`-полів, на чистій базі Odoo 19 CE.
Цей зріз показує, що реально буде в системі, і став заготовкою для A-11. Обсяг розраховано на кілька годин роботи.

## 1. Що показуємо (зв'язок із концепцією)

Наскрізний сценарій: менеджер салону збирає виріб у конфігураторі й бачить ціну → підтверджує замовлення →
для замовлення створюється власна специфікація (BoM) → виробниче замовлення (МО) проходить дільниці «розкрій →
крайкування → присадка → складання» → деталі передаються на розкрій, повертається карта розкрою (імітація) →
плити й обрізки резервуються за партіями, нові ділові обрізки стають залишком із розмірами → планова собівартість
і маржа замовлення.

| Концепція | Що входить у зріз | Чим закрито |
|---|---|---|
| F-03 / S-01 | Виріб з опцій: декор, кромка, фурнітура, розміри + ціна | стандартний конфігуратор `sale` + розмірний коефіцієнт (код) |
| F-04, F-02 / S-02, S-03 | Специфікація з опцій, одна для продажу, розкрою й собівартості | BoM під замовлення (код-генератор поверх стандартного `mrp.bom`) |
| F-06 / S-06, S-07 | МО з власною специфікацією і маршрутом дільниць | стандарт `mrp` (робочі центри, операції, робочі завдання) |
| F-05 / S-04 | Передати деталі на розкрій і отримати карту з відходами | модель `td.mebli.cutting.job`; **розрахунок — імітація** зовнішньої програми |
| F-10 / S-08 | Резерв плити, кромки, фурнітури під замовлення; видно нестачу | стандарт резервування МО + «Стан компонентів»; вибір партій плит — код |
| F-11 / S-09 | Ділові обрізки як залишок із розмірами | стандартні партії `stock.lot` + поля розмірів; обрізки — побічна продукція МО |
| F-14 (план) / S-11 | Планова собівартість і маржа замовлення; план/факт у МО | `sale_margin` + собівартість BoM із `mrp_account` + стандартний «Огляд МО» |
| SC-01 кроки 1–3, SC-02 кроки 4–5, SC-03 (МО), SC-04 кроки 2, 4, 5, SC-05 (план) | Кроки сценаріїв ролей | §6 |

Поза зрізом (свідомо): F-01 (імпорт з PRO100), F-07, F-08, F-09, F-12, F-13 (курс євро), F-15–F-18, S-05, S-10,
S-12–S-14, аналітика (див. §2, рядок «analytic»), імпорт файлу результату реальної програми розкрою (інтерфейс
передбачено, див. §3.3).

## 2. Стандарт Odoo 19, на який спираємось (перевірено у вихідниках)

| Припущення | Підтвердження | Як використовуємо |
|---|---|---|
| Конфігуратор продукту вбудовано в `sale` (окремого `sale_product_configurator` у 19 немає) | `sale/__manifest__.py:73` (assets `product_configurator_dialog`), `sale/controllers/product_configurator.py:10` | діалог вибору опцій у рядку SO |
| Атрибути без варіантів і надбавка до ціни | `product/models/product_attribute.py:24` (`create_variant`), `product/models/product_template_attribute_value.py:36` (`price_extra`) | декор, кромка, фурнітура — `no_variant` з `price_extra` |
| Вільне значення атрибута (поле вводу в конфігураторі) | `product/models/product_attribute_value.py:36` (`is_custom`), `product/models/product_attribute_custom_value.py:17` (`custom_value`, Char), `sale/models/sale_order_line.py:107` (`product_custom_attribute_value_ids`) | ширина / висота / глибина, мм |
| Атрибут з одним вільним значенням показується в діалозі | `sale/static/src/js/product_template_attribute_line/product_template_attribute_line.xml:7`; конфігуратор відкривається, якщо є вільне значення: `product/models/product_template.py:232–245` | 3 атрибути розмірів по одному значенню |
| Ціна рядка рахується в `_compute_price_unit` / `_get_display_price` | `sale/models/sale_order_line.py:589`, `:642` | розмірний коефіцієнт — override `_get_display_price` + доп. depends |
| Процурмент зі SO можна направити на конкретний BoM | `mrp/models/stock_rule.py:138–140` (`values['bom_id']`), `sale_stock/models/sale_order_line.py:284` (`_prepare_procurement_values`) | BoM під замовлення передаємо в `bom_id` |
| МО пов'язане з рядком SO | `sale_mrp/models/mrp_production.py:14` (`sale_line_id`), `sale_mrp/models/stock_rule.py:9`, лічильник `sale_mrp/models/sale_order.py:10` | смарт-кнопка «Виробництво» у SO |
| Пошук BoM фільтрується доменом, який можна розширити | `mrp/models/mrp_bom.py:370` (`_bom_find_domain`), `:385` (`_bom_find`) | BoM під замовлення не знаходяться для інших замовлень |
| MTO-маршрут є, але архівний; маршрут «Виготовити» є | `stock/data/stock_data.xml:42–45`, `mrp/data/mrp_data.xml:10` | дані зрізу активують MTO і ставлять обидва маршрути на вироби |
| Операції на робочих центрах, тривалість, вартість години | `mrp/models/mrp_routing.py:19`, `:27`, `:33`, `:65`; `mrp/models/mrp_workcenter.py:41` | 4 дільниці, тривалість за деталями / метрами кромки |
| Робочі завдання з кнопками старт/стоп є в CE (`mrp_workorder` — Enterprise) | `mrp/models/mrp_workorder.py:667`, `:716`; ENV.md «Недоступні модулі» | дільниці в МО без Enterprise |
| Собівартість BoM з операціями | `mrp_account/models/product.py:63–99` (`_compute_bom_price`, рядок 70 — `opt.cost`) | планова собівартість рядка SO |
| Маржа рядка SO | `sale_margin/models/sale_order_line.py:10–24`; `sale_stock_margin` (auto_install) викликає super для рядків без оцінених рухів: `sale_stock_margin/models/sale_order_line.py:11–17` | `purchase_price` = собівартість BoM замовлення |
| Огляд МО: план / BoM / факт | `mrp/report/mrp_report_mo_overview.py:56–64`, `:485` | план/факт по МО без коду |
| Партії, відстеження | `stock/models/stock_lot.py:42–61`, `stock/models/product.py:851` (`tracking`) | плити й обрізки — партії з розмірами |
| Побічна продукція МО (може бути тим самим товаром, що й компонент; заборонено лише = готовий виріб) | `mrp/models/mrp_bom.py:198–204`, `mrp/models/mrp_production.py:980`, налаштування `mrp/models/res_config_settings.py:10` | обрізок повертається на склад як побічний продукт МО |
| Резервування / зняття резерву | `stock/models/stock_move.py:1034` (`_do_unreserve`), `:2064` (`_action_assign`); стан компонентів МО `mrp/models/mrp_production.py:277`, `:389` | резерв конкретних партій після розкрою |
| Одиниці м² і м (у 19 без категорій, `relative_uom_id`) | `uom/models/uom_uom.py:36–43`, `uom/data/uom_data.xml:55`, `:68` | плита — м², кромка — м |
| Робочі завдання / BoM-ціни групою «Work Orders» | `mrp/models/res_config_settings.py:17` (`group_mrp_routings`) | дані вмикають групу для `base.group_user` |
| Конвенції 19: `models.Constraint`, `res.users.group_ids`, `res.groups.privilege_id`, `lot_producing_ids` | `product/models/product_attribute.py:14`, `odoo/addons/base/models/res_users.py:257`, `odoo/addons/base/models/res_groups.py:36`, `mrp/models/mrp_production.py:120` | код і тести пишемо під 19 |
| analytic: аналітика МО є лише через проєкт (`project_mrp_account`), МО ↔ аналітичний рахунок | `project_mrp_account/__manifest__.py:8`, `mrp_account/models/analytic_account.py:11` | **у зріз не беремо**: собівартість замовлення без проєктів; аналітику — на A-08/A-10 |
| Мова uk_UA, `l10n_ua` є | `base` i18n, каталог `addons/l10n_ua` | інтерфейс — uk_UA через `.po`, `l10n_ua` у зріз не ставимо |

Не перевірено вихідниками і закрито тестом (не вигадуємо): поведінка діалогу конфігуратора з трьома вільними
значеннями (тур `TestConfiguratorTour`), оцінка побічного продукту за стандартною ціною (тест `test_offcut_valuation`).

## 3. Модулі

Мова: рядки коду й подань — англійською, переклад `i18n/uk.po` у кожному модулі; демо-дані — українською (це дані, не
інтерфейс). База показу ставиться з `--load-language=uk_UA`. Версії — `19.0.1.0.0`, ліцензія LGPL-3, автор — ToDo.
Залежності лише від Community; жодних `mrp_workorder`, `web_gantt`, `mrp_maintenance`.

```
td_mebli_mrp ──► td_mebli_sale ──┐
      └────────► td_mebli_cutting ┴─► td_mebli_demo
```

### 3.1 `td_mebli_mrp` — параметричний виріб і BoM під замовлення
`depends: mrp_account, stock`. Без залежності від `sale`: генератор приймає розміри словником і тестується окремо.

Моделі й поля:
- `product.template` (inherit): `td_is_parametric` (Bool), `td_width_nominal/td_height_nominal/td_depth_nominal`
  (Int, мм), `td_width_min/max`, `td_height_min/max`, `td_depth_min/max` (Int), `td_part_rule_ids` (O2m),
  `td_edge_allowance_mm` (Int, default 30). Для матеріалів: `td_material_kind` (Selection: board / edge / fitting),
  `td_sheet_length_mm`, `td_sheet_width_mm`, `td_thickness_mm` (Int), `td_waste_pct` (Float, default 15).
  Constraint (`models.Constraint`): min ≤ nominal ≤ max.
- `product.attribute` (inherit): `td_dimension` (Selection: width / height / depth), `td_component_role`
  (Selection: body_board / facade_board / edge / fitting_set).
- `product.attribute.value` (inherit): `td_component_product_id` (M2o `product.product`) — яку плиту, кромку чи
  комплект фурнітури означає значення.
- `td.mebli.part.rule` (нова; `_order = sequence`): `product_tmpl_id`, `sequence`, `name` (Боковина, Дах…), `qty`,
  `material_role` (body_board / facade_board / fixed), `fixed_material_id` (для ДВП задньої стінки),
  лінійні формули без `safe_eval`: `length = len_w·W + len_h·H + len_d·D + len_const`, так само `width_*`;
  `edge_long_sides`, `edge_short_sides` (0–2). Constraint: результат > 0 на номінальних розмірах.
- `td.mebli.part` (нова, рядки специфікації деталей замовлення): `bom_id`, `rule_id`, `name`, `material_id`, `qty`,
  `length_mm`, `width_mm`, `area_m2` (compute, stored), `edge_product_id`, `edge_length_m` (compute, stored),
  `cutting_job_id` (додає `td_mebli_cutting`).
- `mrp.bom` (inherit): `td_order_bom` (Bool, readonly), `td_template_bom_id`, `td_width/td_height/td_depth`,
  `td_part_ids` (O2m), `td_part_count`, `td_board_area_m2`, `td_edge_length_m`. Override `_bom_find_domain`
  (`mrp/models/mrp_bom.py:370`): `& Domain('td_order_bom', '=', False)`.
- `mrp.routing.workcenter` (inherit): `td_time_basis` (fixed / per_part / per_edge_m / per_board_m2),
  `td_time_rate` (хв на одиницю бази).
- Метод `mrp.bom._td_generate_order_bom(product, dims, selections)` → новий BoM: копія шаблонного BoM виробу
  (операції й постійні рядки), деталі за правилами, рядки плит (м² = Σ площ × (1 + `td_waste_pct`)), рядки кромки
  (м = Σ сторін + припуск), фурнітура з атрибута; `time_cycle_manual` операцій за `td_time_basis`.

Подання: вкладка «Деталі виробу» на формі товару (`invisible="not td_is_parametric"`), поля матеріалу на вкладці
«Запаси»; поля атрибута й колонка компонента у списку значень атрибута; на формі BoM — банер «Специфікація під
замовлення», вкладка «Деталі» (список `td.mebli.part`), підсумки площі/кромки; у списку операцій — база й норма часу.
Меню: «Виробництво → Налаштування → Правила деталей» (список `td.mebli.part.rule`, групування за виробом).
Права: `mrp.group_mrp_user` — читання правил і деталей, запис деталей; `mrp.group_mrp_manager` — повні.

### 3.2 `td_mebli_sale` — конфігуратор, ціна, передача у виробництво, планова собівартість
`depends: td_mebli_mrp, sale_mrp, sale_margin` (`sale_stock_margin` ставиться сам — auto_install).

- `sale.order.line` (inherit): `td_width/td_height/td_depth` (Int, compute stored з
  `product_custom_attribute_value_ids` за `td_dimension`, readonly=False), `td_size_factor` (Float, compute stored:
  (W·H)/(W₀·H₀), межі задає min/max виробу), `td_bom_id` (M2o `mrp.bom`, copy=False),
  `td_planned_material_cost`, `td_planned_operation_cost` (Monetary, stored).
  `@api.constrains`: розміри в межах min/max виробу, вільне значення — ціле число мм.
  Override `_get_display_price` (`sale/models/sale_order_line.py:642`): ціна прайсу (з `price_extra`) × `td_size_factor`;
  `_compute_price_unit` — додати `@api.depends('td_width','td_height')`.
  `action_td_generate_bom()` — кнопка «Сформувати специфікацію» в рядку (чернетка); при підтвердженні —
  автоматично в `_action_launch_stock_rule` (`sale_stock/models/sale_order_line.py:387`) до super.
  `_prepare_procurement_values` (`sale_stock/models/sale_order_line.py:284`): `values['bom_id'] = td_bom_id`.
  `_compute_purchase_price` (`sale_margin/models/sale_order_line.py:21`): для параметричних рядків —
  `product._compute_bom_price(td_bom_id)` (`mrp_account/models/product.py:63`).
- `mrp.bom` (inherit): `td_sale_line_id` (M2o, readonly, index), `td_sale_order_id` (related).
- Подання: у рядках SO — необов'язкові колонки розмірів і коефіцієнта, кнопка «Специфікація» (відкриває BoM);
  на формі BoM — посилання на замовлення. Звіт «Собівартість замовлень» (pivot + list по `sale.order.line`,
  домен — параметричні вироби; міри: сума, планові матеріали, планові операції, маржа, маржа %).
  Меню: «Продажі → Звітність → Собівартість замовлень». Права: читання звіту — `sales_team.group_sale_salesman`.

### 3.3 `td_mebli_cutting` — розкрій і ділові обрізки
`depends: td_mebli_mrp, stock`.

- `td.mebli.cutting.job` (нова, `mail.thread`): `name` (послідовність `CUT/`), `state`
  (draft → sent → result → done / cancel), `production_ids` (M2m `mrp.production`), `part_ids` (O2m деталей з
  BoM вибраних МО), `sheet_ids` (O2m), `kerf_mm` (4), `trim_mm` (10), `min_offcut_mm` (300),
  `result_source` (Selection: simulated / imported) — **показується банером «Результат отримано з імітації програми
  розкрою»**, `waste_pct` (compute), `export_attachment_id`.
  Кнопки: «Передати на розкрій» (`action_send`: CSV деталей у форматі, близькому до поширених програм розкрою —
  матеріал, довжина, ширина, к-сть, кромки, замовлення; файл — `ir.attachment`), «Отримати результат (імітація)»
  (`action_simulate`), «Провести» (`action_done`).
  Єдина точка входу результату — `_td_apply_result(payload: dict)`; імітатор і майбутній імпорт реальної програми
  (A-11) подають однаковий `payload` — заміна імітації не змінює моделі.
- `_td_simulate_optimizer()` — **імітація**: детермінований смуговий розкрій «спершу найбільші», пропил і обрізка
  країв; спершу пробує наявні ділові обрізки того ж матеріалу, потім цілі листи; залишок ≥ `min_offcut_mm` по обох
  сторонах — діловий обрізок, решта — відхід. Не претендує на оптимальність (концепція: «оптимізація власними засобами
  Odoo — поза концепцією»).
- `td.mebli.cutting.sheet`: `job_id`, `product_id` (плита), `lot_id` (лист або обрізок, з якого кроїмо),
  `length_mm`, `width_mm`, `used_area_m2`, `waste_pct`, `placement_ids` (деталь, x, y, поворот),
  `offcut_ids` (O2m `td.mebli.cutting.offcut`: length, width, area, `lot_id` після проведення).
- `stock.lot` (inherit): `td_length_mm`, `td_width_mm`, `td_is_offcut`, `td_cutting_job_id`, `td_area_m2` (compute).
- `mrp.production` (inherit): `td_cutting_job_ids`, смарт-кнопка «Розкрій».
- `action_done`: для кожного МО — зняти резерв плит (`_do_unreserve`), створити рядки руху на партії листів/обрізків
  пропорційно площі деталей, додати побічні рухи (`move_byproduct_ids`) з новими партіями-обрізками
  (`td_is_offcut=True`, розміри, назва `OFF-<декор>-<N>`); кромка й фурнітура резервуються стандартно.
- Подання: список/форма/пошук завдань (фільтри за станом, матеріалом), форма листа з розміщенням (таблиця, без
  графіки), список «Ділові обрізки» (`stock.lot`, домен `td_is_offcut`, колонки довжина × ширина, площа, залишок,
  групування за товаром-декором), розміри на формі партії.
  Меню: «Виробництво → Розкрій → Завдання розкрою», «Склад → Продукти → Ділові обрізки». Кнопка «Створити
  завдання розкрою» — дія сервера на списку МО.
- Права: `mrp.group_mrp_user` — створення й робота із завданнями; `stock.group_stock_user` — читання завдань і
  обрізків; `mrp.group_mrp_manager` — скасування й видалення.

### 3.4 `td_mebli_demo` — каталог і склад для показу
`depends: td_mebli_sale, td_mebli_cutting`. Дані в ключі `data` (шаблон баз — без демо, `--without-demo=True`);
модуль клієнтам не ставиться (позначити в `description` і README). Усі назви брендів **вигадані**.

- Налаштування: група `mrp.group_mrp_routings`, `mrp.group_mrp_byproducts`, `stock.group_production_lot`,
  `product.group_product_variant` для `base.group_user`; активувати `stock.route_warehouse0_mto`; валюта компанії
  UAH (у `post_init_hook`, лише якщо ще немає проводок).
- Плити ДСП 16 мм (м², партії, лист 2800×2070, відходи 15 %): «Egren E1145 Дуб Сонома», «Kronvald K101 Білий
  гладкий», «Kronvald K190 Антрацит»; МДФ 18 мм фасадна «Egren MF-01 Білий матовий»; ДВП 3 мм біла. Ціни 85–950 грн/м².
- Кромка ПВХ (м): 0,4×19 і 2×22 під кожен декор (6–22 грн/м).
- Фурнітура (шт): «Bluma — комплект петель з доводчиком», «Hetta Slide — розсувна система для шафи-купе»,
  «Bluma — напрямні повного висування, к-т для комода», «Опори регульовані к-т». Одну позицію заведено з нестачею,
  щоб у МО було видно «Немає в наявності».
- Атрибути: «Декор корпусу» (3, `price_extra` 0 / +600 / +900), «Декор фасаду» (2), «Кромка» (0,4 мм / 2 мм +350),
  «Фурнітура» (Стандарт / Преміум +2500), «Ширина, мм», «Висота, мм», «Глибина, мм» (вільні значення).
- Вироби (маршрути «Виготовити» + MTO, `td_is_parametric`): «Шафа-купе 2-дверна» 1600×2400×600 (28 000 грн,
  7 правил деталей), «Комод 4 шухляди» 800×850×450 (9 500 грн, 6 правил), «Кухонний модуль нижній 600»
  600×720×560 (5 200 грн, 5 правил). Шаблонний BoM кожного — 4 операції.
- Робочі центри: Розкрій (650 грн/год, на деталь 1,5 хв), Крайкування (550, 0,6 хв/м), Присадка (500, 1 хв/деталь),
  Складання (400, фіксовано 45–90 хв).
- Залишки (через `stock.quant` + `action_apply_inventory`, `stock/models/stock_quant.py:441`): по 6–10 листів на
  декор (партії листів), 2 ділові обрізки «Дуб Сонома» (1200×700, 900×450), кромка 300–500 м.
- Покупець: «Салон «Демо», покупець 1» (без ПІБ і контактів).
- `scripts/show_scenario.py` (запуск через `odoo-bin shell`): відтворює сценарій §6 до кожного кроку — щоб
  скриншоти можна було перезняти на чистій базі.

## 4. Тести

Запуск: `F3D_ADDONS_DIR=/home/user/industry-flow-test-mebli/package/addons F3D_TEST_INSTALL=td_mebli_demo
/home/user/f3d/factory3d/tools/odoo/run_tests.sh mebli_t1 /td_mebli_mrp,/td_mebli_sale,/td_mebli_cutting`.
Тести мають власні фікстури (не залежать від `td_mebli_demo`); тести, що зачіпають модулі поза `depends`, —
`@tagged('post_install', '-at_install')` (ENV.md «Особливості Odoo 19»). Перед здачею — `boost:odoo19-lint`.

| Модуль | Клас / тест | Що перевіряє |
|---|---|---|
| mrp | `TestPartRules.test_dims` | довжина/ширина деталей за лінійними формулами на номінальних і крайніх розмірах; правило з результатом ≤ 0 — ValidationError |
| mrp | `TestOrderBom.test_generate` | рядки плит (м² з відходом), кромки (м з припуском), фурнітура; операції скопійовано, `time_cycle_manual` за базою |
| mrp | `TestOrderBom.test_bom_find_excludes_order_bom` | `_bom_find` повертає шаблонний BoM, а не BoM замовлення |
| mrp | `TestOrderBom.test_bom_cost` | `_compute_bom_price` = матеріали + операції (ручний розрахунок) |
| sale | `TestSaleLine.test_dims_from_custom_values` | розміри з вільних значень; нечислове значення чи вихід за межі — ValidationError |
| sale | `TestSaleLine.test_price` | ціна = (ціна + `price_extra`) × коефіцієнт розміру; ручна ціна не перезаписується |
| sale | `TestSaleFlow.test_confirm_creates_mo` | після підтвердження: BoM замовлення, МО з `bom_id` і `sale_line_id`, 4 робочі завдання, лічильник МО в SO |
| sale | `TestSaleFlow.test_two_orders_two_boms` | два замовлення того самого виробу з різними розмірами → два BoM, два МО, без змішування |
| sale | `TestSaleFlow.test_margin` | `purchase_price` = собівартість BoM замовлення; маржа рядка |
| sale | `TestConfiguratorTour` (HttpCase, post_install) | у формі SO діалог конфігуратора показує 3 поля розмірів, рядок отримує розміри й ціну |
| cutting | `TestSimulator.test_deterministic` | однакові деталі → однакова карта; пропил і обрізка враховані; % відходу в межах |
| cutting | `TestSimulator.test_offcut_reuse_first` | деталь, що вміщується в наявний обрізок, кроїться з нього, а не з нового листа |
| cutting | `TestCuttingDone.test_reserve_and_offcuts` | після «Провести»: рухи плит на вибрані партії, нові партії-обрізки з розмірами як побічна продукція; після завершення МО обрізок є в залишку |
| cutting | `TestCuttingDone.test_offcut_valuation` | оцінка обрізка за стандартною ціною плити (перевіряє припущення §2) |
| cutting | `TestAccess.test_stock_user_readonly` | комірник читає завдання, але не проводить |

Критерій готовності зрізу: усі тести зелені, `boost:odoo19-lint` без помилок, модулі встановлюються на чисту базу
шаблону, сценарій §6 проходить вручну в uk_UA без повідомлень про помилки.

## 5. Що позначено як імітація

| Що | Як позначено в інтерфейсі | Що буде в A-11 |
|---|---|---|
| Розрахунок карти розкрою (`_td_simulate_optimizer`) | банер на формі завдання й листа «Результат отримано з імітації програми розкрою», поле «Джерело результату = Імітація» | імпорт файлу реальної програми в той самий `_td_apply_result` |
| Файл «Передати на розкрій» | у назві вкладення «формат-чернетка» | формат обраної клієнтом програми |
| Специфікація з правил деталей замість файлу програми проєктування (F-01) | у банері BoM «згенеровано з опцій замовлення» | імпорт PRO100/ін. — окрема функція |
| Каталог, бренди, ціни, залишки | модуль `td_mebli_demo`, у назвах брендів — вигадані марки | майстер-дані A-13 |

## 6. Сценарій показу і скриншоти

Фактичний показ — 16 кроків від імені п'яти ролей (деталі й зв'язок із болями PAIN-xx — таблиця в `README.md`, історія для власника — `SHOW.md`).
Збірка: `shoot/build_db.sh mebli_demo` (модулі, uk_UA, `seed_showcase`), `serve.sh mebli_demo 19071`, `node shoot/scenario.mjs 19071`
(Playwright, viewport 1440x900, скриншоти deviceScaleFactor 2, відео 1440x900 (webm; вхід кожної ролі — з попередньо збережених сесій, сторінка входу в кадр не потрапляє; заставки — окремі повноекранні сторінки)). Файли — `screens/NN-<назва>.png`.

Кроки: 1 виріб і опції; 2 конфігуратор; 3 «а якщо ширше» + специфікація; 4 ціна й маржа; 5 комерційна пропозиція; 6 підтвердження і МО в замовленні;
7 дошка замовлень; 8 список МО; 9 нестача фурнітури; 10 завантаження дільниць; 11 завдання розкрою; 12 карта розкрою й економія; 13 ділові обрізки;
14 план/факт («Огляд МО»); 15 час до запуску; 16 маржа замовлень.

## 7. Розкладка коду й порядок робіт

`package/addons/td_mebli_{mrp,sale,cutting,demo}/` — стандартна структура (`__manifest__.py`, `models/`, `views/`,
`security/ir.model.access.csv`, `data/`, `i18n/uk.po`, `tests/`, `README.md`). `tests` не імпортувати з `__init__.py`.

1. `td_mebli_mrp` + тести (генератор BoM — ядро зрізу).
2. `td_mebli_sale` + тести, включно з туром конфігуратора.
3. `td_mebli_cutting` + тести (паралельно з п. 2 після п. 1).
4. `td_mebli_demo` + `show_scenario.py`, база `mebli_show`, скриншоти, `SHOW.md`.
5. `boost:odoo19-lint`, `.po`, повний прогін тестів; git і PR — менеджер.

## 8. Відкриті питання (до людини)

1. Ціна від розміру: коефіцієнт за площею фасаду (W·H) — прийнятне спрощення чи потрібна ціна за прайсом розмірних
   кроків? У зрізі — коефіцієнт.
2. Ціна в діалозі конфігуратора показується без розмірного коефіцієнта (діалог — стандартний OWL); повна ціна — у
   рядку після додавання. Розширювати діалог у A-11 чи лишити?
3. Обрізок як побічна продукція МО з партією проти окремого товару «Обрізок» — у зрізі перше (пошук за декором).
4. Аналітика (`project_mrp_account`, проєкт на замовлення) у зріз не входить — чи потрібна на показі?
