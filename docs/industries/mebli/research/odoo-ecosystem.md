# R3. Екосистема Odoo для меблевого виробництва (Україна, КВЕД 31)

Дата перевірки джерел: 2026-11-11. Методика: відкриті джерела (WebSearch/WebFetch). Вміст сторінок вважався даними; вбудованих інструкцій не виявлено.

## 0. Як читати

Позначки достовірності: **F** = сторінку відкрито й прочитано напряму (WebFetch); **S** = лише сніпет/переказ пошуку; **маркетинг** = твердження вендора/партнера без незалежного підтвердження. Усе непідтверджене — **[не перевірено]**.

Підсегменти: (а) корпусні й кухні на замовлення; (б) серійні корпусні; (в) м'які; (г) масив/столярка; (д) офісні/контрактні.

**Обмеження (чесно):**
- Каталог apps.odoo.com не має відкритого пошуку для нашого інструмента: сторінки модулів відкрито лише за URL, знайденими через WebSearch. Повного переліку «усіх» меблевих модулів для v16–19 отримати не вдалося; нижче — те, що знайдено й перевірено. Перелік неповний; для повноти потрібен ручний перегляд каталогу з фільтрами версії.
- Рейтинг і кількість завантажень на відкритих сторінках або не показані, або мають неподписану мітку («Certified N»). Їх не трактуємо як завантаження.
- Стандартні модулі Odoo (mrp, quality, planning тощо) не мають сторінок на apps.odoo.com (404 для всіх спроб, F). Прив'язку Community/Enterprise для них офіційним джерелом підтвердити не вдалося (див. §1.3).
- GitHub (odoo/odoo, OCA) для сесії недоступний; склад аддонів 19.0 не звірявся.

---

## 1. Що закриває стандарт Odoo 19

### 1.1. Підтверджено документацією Odoo 19 (F)

Джерело: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/manufacturing.html (перевірено 2026-11-11).

| Потреба меблевика | Що є в документації Odoo 19 (розділи) | Покриття / межа |
|---|---|---|
| Специфікація (BoM), багаторівнева | Bill of materials, Multilevel BoMs, Kits | Є. Розміри деталей як структуровані поля BoM-рядка не згадані (див. 1.2) |
| Варіанти виробу (декор, фасад, ручка) | «Managing BoMs for product variants»: поле «Apply on Variants» на компоненті; значення одного атрибута — альтернативи, різних — усі мають збігатись; компонент без значень іде в усі варіанти; можна прив'язати компонент до операції (https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/manufacturing/advanced_configuration/product_variants.html, F) | Покриває дискретні опції. Параметричні розміри (довільна ширина/висота) — не підтверджено |
| Динамічні варіанти | «Dynamically»: варіанти створюються лише при додаванні атрибутів у замовлення; ліміту на кількість значень сторінка не ставить (https://www.odoo.com/documentation/19.0/applications/sales/sales/products_prices/products/variants.html, F) | Знімає «вибух» варіантів; не рахує ціну від розмірів |
| Маршрути/операції, робочі центри | Work centers, Work order dependencies, Shop Floor (+ time tracking), 1/2/3-step manufacturing | Є; різання/кромка/присадка/збірка моделюються як операції |
| Незавершене виробництво, собівартість | Manufacturing order costs, Work-in-progress costs | Є розділи; глибину собівартості по замовленню не перевірено |
| Планування | Master production schedule, Work center time off, backorders, split/merge MO | Розділи є; MPS — перевірити edition [не перевірено] |
| Субпідряд (фарбування, оббивка на стороні) | Subcontracting: basic, resupply, dropship | Є |
| Партії/серії, прослідковуваність | Manufacture with lots and serial numbers | Є; пакет даних EUDR для імпортера в ЄС (геолокація, документи походження, кількість за партією) — td_ поверх лотів; декларацію подає імпортер, а не виробник (R7, FUNCTIONAL-MAP D-15) [формат обміну не перевірено] |
| Брак, відходи, побічні продукти | Scrap during manufacturing, By-products, Unbuild, Dismantle | Є; ділові залишки плит як облікові одиниці — не підтверджено |
| Звітність | Delays, Allocation, OEE, Production analysis | Є |

Quality (https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/quality.html, F): quality control points, checks, alerts, failure locations; типи перевірки: Instructions, Pass/Fail, Measure, Take a Picture. Підходить для контролю фасадів/кромки/кінцевого огляду.

PLM (https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/plm.html, F): призначення — тестування/співпраця/ітерації; у змісті — ECO (engineering change orders), версії, погодження. Не встановлюється з Manufacturing за замовчуванням. Для масового меблевого виробництва це зміна специфікацій; для меблів на замовлення — малоймовірний пріоритет [висновок, не факт].

Maintenance (https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/maintenance.html, F, лише індекс): облік обладнання, календар, запити на обслуговування. Корисно для ЧПУ/крайкооблицювальних верстатів; деталі профілактики/MTBF сторінка не розкриває.

Field Service (https://www.odoo.com/documentation/19.0/applications/services/field_service.html, F, лише індекс): задачі, product management, маршрут (itinerary), worksheets. Для монтажу меблів (підсегмент а, д) — основа; підпис клієнта, інвойс з місця — не підтверджено на цій сторінці [не перевірено].

Planning (https://www.odoo.com/documentation/19.0/applications/services/planning.html, F): ресурси (співробітники й матеріали/обладнання), ролі, шаблони змін, Gantt, відкриті зміни й Auto Plan, зв'язок із Sales/Project. Придатно для графіка бригад монтажників і завантаження обладнання.

Studio (https://www.odoo.com/documentation/19.0/applications/studio.html, F): зміна полів/видів/моделей без коду, автоматизації, звіти PDF, правила погодження. Сторінка згадує, що встановлення на тарифі Standard запускає апсел на Custom. Це опосередковано вказує, що Studio платний на рівні Odoo Online; Enterprise-статус — нижче.

### 1.2. Прогалини стандарту для меблів (підтверджено джерелами)

- **Розкрійні розміри в BoM.** Форум Odoo (v17): відповідь «стандартний спосіб» — окремий продукт на кожну деталь із розміром у назві; автор потоку розширив Shopfloor, додавши ширину/довжину/товщину в BoM-рядки, «здивований, що цього немає за замовчуванням» (https://www.odoo.com/forum/help-1/creating-cut-lists-for-cnc-sawing-245070, F, форум).
- **Пакетна обробка спільних операцій.** Форум: різання меламіну й кромкування ефективні партією за кольором між МО, а маршрути Odoo ідуть на кожне МО; «MRP Group» групує лише за продуктом/BoM; пропонували `mrp_bom_attribute_match` (Odoo 18) — як відправну точку, не підтверджене рішення (https://www.odoo.com/forum/help-1/batch-processing-in-mrp-for-shared-material-steps-eg-cutting-melamine-by-color-across-multiple-mos-without-per-mo-execution-287366, F, форум, дата питання не вказана [не перевірено]).
- **Розкрій (nesting).** Консалтингові сторінки стверджують, що стандартний MRP не має розкладки розкрою, втрат на пропил і обліку ділових залишків (S, маркетинг партнерів; https://doodex.net/manufacture/par-secteur/mobilier-cnc). Це збігається з відсутністю розкрою на галузевій сторінці Odoo (нижче).

### 1.3. Community vs Enterprise

**Не підтверджено офіційно.** Спроба відкрити https://www.odoo.com/page/editions (F): таблиця перелічує MRP (Shopfloor, Control Panel, Scheduling), PLM, Quality, Maintenance (розділ Supply Chain), Planning, Field Service (Services), Studio (Customization), але позначки Community/Enterprise у вилучений текст не потрапили. MPS на сторінці не згадується.

Непрямі підтвердження (F, apps.odoo.com): галузеві пакети Odoo `custom_furniture` і `carpenter` мають ліцензію OEEL-1/OPL-1 і «потребують Odoo Enterprise»; залежності `custom_furniture` — Planning, Quality, Field Service, Studio, Timesheets, Project, Manufacturing (https://apps.odoo.com/apps/modules/saas-18.1/custom_furniture). Це не доводить, що кожен із цих модулів окремо Enterprise-only, але сам пакет — Enterprise.

Сторонні порівняння (S, блоги партнерів на старіших версіях 10–17, часто суперечать одне одному): PLM, Planning, Studio — лише Enterprise; Quality і Maintenance — розбіжності; MPS — залежить від версії (https://www.cybrosys.com/odoo/compare-odoo-community-vs-enterprise/, https://ecosire.com/blog/odoo-community-vs-enterprise та ін.). Для v19 вважати **[не перевірено]**; перед рішенням про Community/Enterprise звірити таблицю на живій сторінці odoo.com/page/editions або склад каталогів addons 19.0 vs enterprise.

Робоча гіпотеза для пакета (позначена як гіпотеза): Community = Inventory, Sales, Purchase, базовий MRP (BoM, MO, робочі центри); Enterprise = PLM, Quality, Planning, Field Service, Studio, Shop Floor-розширення. Перевірити.

### 1.4. Конфігуратор виробів

- Стандарт Odoo 19: варіанти з атрибутами та «Apply on Variants» в BoM; сторінка документації про Product Configurator/grid entry у прочитаній частині не знайдена [не перевірено; на сторінці про варіанти Product Configurator і grid entry не згадані (прочитано весь текст)].
- На галузевій сторінці Odoo «Custom Furniture Production» окремого конфігуратора немає; ближче — варіанти й гнучкі BoM (https://www.odoo.com/industries/custom-furniture-production, F, 2026-11-11). Параметричний конфігуратор (довільні розміри → BoM → ціна) — зона сторонніх модулів (§2).

### 1.5. Галузеві пакети самого Odoo (F)

Обидва — Odoo S.A., ліцензія OEEL-1/OPL-1, потребують Enterprise, ціна на сторінці не вказана (доступні варіанти 18.0, 19.0, saas-19.x, 20.0).

| Пакет | Опис на сторінці | Залежності | Джерело |
|---|---|---|---|
| `custom_furniture` («Custom Furniture Production») | інтер'єрні/меблі на замовлення; CRM, Sales, Project і Field Service, Inventory, Manufacturing, Planning, Timesheets, Invoicing; «лише стандартні функції без коду» | CRM, Calendar, Employees, Knowledge, Planning, Quality, Contacts, Discuss, Field Service, Studio, Timesheets, Project, Manufacturing, Inventory, Accounting, Invoicing, Purchase, Sales | https://apps.odoo.com/apps/modules/saas-18.1/custom_furniture |
| `carpenter` («Carpenter») v19.0 | Quoting, Project Management, Manufacturing, Purchasing & Inventory; «Certified 637» (мітка без підпису) | CRM, Calendar, Contacts, Discuss, Documents, Employees, Purchase, Invoicing, Inventory, Knowledge, Project, Sales, Manufacturing, base_industry_data | https://apps.odoo.com/apps/modules/19.0/carpenter |
| `furniture_store` v17.0 (роздріб) | «встановлює меблевий магазин для продажу стільців, диванів, обідніх столів»; «Certified 2471» (мітка без підпису) | Knowledge, Manufacturing, CRM, Website, Calendar, Contacts, Discuss, Inventory, Sales, Invoicing, POS, eCommerce, Purchase | https://apps.odoo.com/apps/modules/17.0/furniture_store |

Маркетингова сторінка (https://www.odoo.com/industries/custom-furniture-production, F): заявлено quotation builder, проєкти/задачі після продажу з погодженнями та монтажем, змінні BoM, capacity planning, контроль якості, варіанти, worksheets для робіт на місці. **Не згадано:** розкрій, CAD, окремий конфігуратор, окремий Field Service. Це маркетинг; конкретну глибину функцій не підтверджено.

Висновок для підсегментів: пакети Odoo — це «шаблон налаштування» стандартних додатків (за власним описом), а не меблева функціональність. Покриття (а) — часткове, (г) — часткове, (б), (в), (д) — окремих рішень не знайдено.

---

## 2. Сторонні модулі й рішення партнерів (Odoo Apps Store та вендори)

Колонки: Назва / автор / версії / ціна / edition / функції / рейтинг-завантаження / докази. «Ціна» — як на сторінці на дату перевірки (ціни в сторі динамічні, на різних датах/запитах показувались різні числа: див. примітки).

### 2.1. Конфігуратори і виробництво на замовлення

| Модуль | Автор | Версії | Ціна | Edition/ліцензія | Функції (за сторінкою) | Рейтинг / завантаження | Докази |
|---|---|---|---|---|---|---|---|
| Make-to-Order Product Configurator `make_to_order_configurator` | Pokutsoft | 18.0 (сумісний з 19.0; також 19.0, 20.0), оновлено 2026-10-06 | $215.46 | Community і Enterprise; OPL-1 | «Configure-to-order engine»: ціна + реальна BoM і маршрут; формули кількості компонентів; розв'язувач обмежень; групи опцій з доплатою/собівартістю; залежності й виключення опцій; тривалість операцій | не показано | F (https://apps.odoo.com/apps/modules/18.0/make_to_order_configurator); скриншотів не описано |
| CPQ — Dynamic Product Configurator `ec_cpq` | Ensigncode Software | 19.0 | $96.73 (інший пошуковий сніпет: $99.94 — розбіжність) | мітка «Enterprise Community» без пояснення; LGPL-3 | конфігуратор над будь-яким продуктом, min/max/default кількості, опційні позиції, Manufacture/Kit BoM, спливаюче вікно у SO, прайс-листи, створення MO/поставок/закупівель; 90 днів підтримки | не показано | F (https://apps.odoo.com/apps/modules/19.0/ec_cpq); не меблевий; 811 рядків коду |
| Product Configurator on Production Order `fal_production_order_product_configurator` | CLuedoo | 17.0, 18.0, 19.0 | $777.37 (інший сніпет: $800.01 — розбіжність) | Enterprise; OPL-1 | конфігуратор варіанту прямо у виробничому замовленні | не показано | F (https://apps.odoo.com/apps/modules/19.0/fal_production_order_product_configurator); 8884 рядки; залежить від «Advanced Product Configurator» та інших |
| `fal_advanced_product_configurator`, `fal_mrp_product_configurator`, `fal_repair_product_configurator` | CLuedoo (за іменуванням) | 18.0, 19.0 | [не перевірено] | [не перевірено] | — | — | лише S (URL у видачі) |
| OCA `product_configurator` (+ `_mrp`, `_sale`) | OCA | 18.0 (1.0.0, beta), 19.0 — **не підтверджено** | безкоштовно (OCA) | LGPL/AGPL [не перевірено] | базовий конфігуратор-візард; MRP-інтеграція | — | S: https://pypi.org/project/odoo-addon-product-configurator-mrp/18.0.1.0.0.5/ і https://odoo-modules.trobz.com/oca/product-configurator/18.0/product_configurator.html; гілка 19.0 не підтверджена |
| `product_variant_configurator` | OCA/product-variant | 12.0–19.0 | безкоштовно [не перевірено] | Third Party | — | — | S: https://apps.odoo.com/apps/modules/19.0/product_variant_configurator; функції не читались |
| `mrp_bom_attribute_match` | не встановлено (рекомендував Cybrosys на форумі) | 18.0 | [не перевірено] | [не перевірено] | операції/варіанти BoM за атрибутом | — | S (форум) |

### 2.2. Розкрій / оптимізація

| Модуль | Автор | Версії | Ціна | Edition/ліцензія | Функції | Рейтинг / завантаження | Докази |
|---|---|---|---|---|---|---|---|
| MI ERP — Cutting Optimizer `mierp_cutting_optimizer` | MI ERP APP / GRUPO MI ERP SAS (https://www.mi-erp.app) | 19.0 | $2943.84 (інший сніпет: $3000 — розбіжність) | Community і Enterprise; ліцензія не прочитана | 1D (бруси/труби) CP-SAT/FFD з пропилом і кількома довжинами заготовок; 2D (листи): guillotine+backtracking, CP-SAT, rectpack, NFDH; обрізки та обертання; SVG-розкладки (OWL 2); PDF по аркушу з переліком деталей; кнопка в SO (оновлює рядки замовлення) і створення MO; залишки ≥5 см зберігаються як складські; REST `POST /api/v1/cutting/optimize` (Bearer); multi-company; ліміт часу 30 с; **врахування напряму текстури — заявлено в описі**; **кромка — не згадана** | не показано | F (https://apps.odoo.com/apps/modules/19.0/mierp_cutting_optimizer); скриншотів немає; 2969 рядків; залежить від Python-пакета `rectpack`, рекомендовано `ortools`; маркетинг; реальну якість розкрою не перевірено |
| LaserCAM Connector `lasercam_connector` | UCASE MB (https://laser.ucase.eu) | 15.0 (модуль 15.0.5.5.0); заявлено підтримку Odoo 9.0–20.0 | на сторінці не вказана | LGPL-3; Third Party | nesting BoM на листи, суміш деталей з кількох BoM на одному листі; CNC-фрези для дерева/пластику/композитів; пряме надсилання в LaserCAM (11.0+), зворотний запис — функція LaserCAM Pro; створення продуктів із DXF; ZIP-обмін; розгортка STEP (Pro) | не показано; «27» без підпису | F (https://apps.odoo.com/apps/modules/15.0/lasercam_connector); текстура — не згадана, кромка — не згадана явно; це лазерний/CNC-розкрій, не меблева плита; працює разом із зовнішнім LaserCAM (платним [не перевірено]) |
| Cutting Optimizer (рішення на odoo.com) «Affordable Panel Cutting» | soft---troopers.odoo.com | — | — | — | S: «автономне ПЗ для розкрою панелей поза Odoo» | — | https://soft---troopers.odoo.com — не читалось [не перевірено] |
| Metal Fabrication Management / ECOSIRE Metal Fabricator | Probuse / ECOSIRE | 19.0 | — | — | оцінка вартості (Probuse); nesting листа/бруса й облік залишків (ECOSIRE) | — | S; **не меблеві** |
| POS Cutting Orders `ma_pos_cutting` | xamltech | 18.0 | ≈$448 (S) | лише Odoo Online (S) | відділ різання тканин/текстилю в POS | — | S; роздріб тканин, не виробництво меблів |
| Textile Management `textile_management` | Cybrosys | 19.0 | [не перевірено] | AGPL-3 | залежить від MRP; деталі не прочитано | — | S; потенційно для підсегмента (в) — [не перевірено] |
| `plm_cutted_parts` | [не перевірено] | 9.0 | — | — | — | — | S (URL у видачі); застарілий |

### 2.3. Продукти ECOSIRE (build-to-order, не завантажуваний додаток)

Перевірено напряму (F). Це **послуга**: розробка під замовлення за скопінгом; на сторінках немає клієнтів, кейсів, скриншотів (лише «Illustrative preview»); версії/тестування — самозаявлені; ліцензія «Licence confirmation required».

| Продукт | Ціна (орієнтовна) | Версії / edition | Функції (заявлені) | URL |
|---|---|---|---|---|
| Custom Furniture Production | від $999 | 17, 18, 19; Community (функції, що потребують Enterprise-додатків, позначаються на скопінгу) | специфікація MTO, прив'язана до рядків SO (розмір, матеріал, фініш, профіль краю, фурнітура); параметрична BoM; допуск на відходи; калькуляція під час пропозиції; автогенерація MO; цехові звіти cut list і spec sheet; ролі доступу; XML-RPC/JSON-RPC | https://ecosire.com/apps/odoo/custom-furniture-production |
| Carpentry Business Configuration (`carpenter` на ecosire.com) | від $999 | 17, 18, 19; Community і Enterprise (розширений MRP і повний облік — Enterprise) | початкові категорії/шаблони (деревина, плитні матеріали, профілі, кромка, кріплення); робочі центри (різання, кромкування, збірка, шліфування, оздоблення, монтаж); шаблони BoM для корпусів, дверей, стільниць, сходів; MO автоматично при підтвердженні квоти | https://ecosire.com/apps/odoo/carpenter |
| Furniture & Made-to-Order Configurator | від $999 (S-видача давала $799 — розбіжність) | 17, 18, 19; Community/Enterprise | BoM на етапі пропозиції з опцій (без передзавдання варіантів); опції → компоненти й операції (напр. лакування додає кроки); ціна з компонентів і праці; PDF cutting list і вихід sheet-yield (nesting) — заявлено; правила залежностей/виключень | https://ecosire.com/apps/odoo/odoo-furniture-mto-configurator |

Висновок: за ECOSIRE «розкрій» заявлений, але алгоритм і якість не підтверджено; кромка/напрям текстури не вказані [не перевірено].

### 2.4. Партнери Odoo з меблевим фокусом (маркетинг партнерів, S/F)

- **Doodex** (Official Partner з 2018 за власним описом; реф. у Індонезії): BoM-конфігуратор для меблів із багатьма рівнями; пакетне виробництво; трасованість лота деревини; «5–12 пунктів валової маржі від мінімізації відходів» (приклад 8.3% vs 14.2%) — **маркетинг, вендор-звіт**; «готового CAM-конектора немає, кожна інтеграція — розробка» (AlphaCAM, Vectric, Mastercam, EzyNest/Cabinet Vision, оптимізатори Cut Master/OptiCut/OptiNest); панельний оптимізатор — 2–4 тижні; пакет проєкту $4–6 тис./міс. 8–16 міс., підтримка $300–1200/міс. Джерело: https://doodex-prod.pages.dev/manufacture/par-secteur/mobilier-cnc (F), також https://doodex.net/manufacture/par-secteur/mobilier-cnc (S).
- **VentorTech**: «спеціального меблевого модуля немає», пропонує комбінувати MRP, Inventory, Sales, Purchase, PLM, Website, CRM; потік «design-to-order» (візит, дизайн, кошторис, погодження, виробництво, доставка, монтаж, підпис); названий конектор 2020KD (S, кастомний, не публікується у сторі); терміни 3–8 міс.; орієнтовна вартість $10–15 тис. (≈12 користувачів), $40–80 тис. (≈56), від $150 тис. (≈300) без ліцензій Odoo — маркетинг. CAD/ЧПУ/розкрій на сторінці **не згадані**. Джерело: https://ventor.tech/industries/manufacturing/odoo-for-furniture-kitchen-and-bathrooms-manufacturing/ (F).
- **Callista** (Бельгія): конектор **Winner Design → Odoo** (кухонне/столярне ПЗ Winner Design залишається майстром номенклатури/ціни/поставки; в Odoo — закупівля матеріалів, виробництво шаф, планування монтажу, інвойси; документація для монтажників). Версія не вказана [не перевірено]. Джерело: https://www.callista.be/en/modules-detail-winner-design (F); також https://www.callista.be/en/po-keukenbouw (S).
- **Webkul**: кейс Best Online Cabinets (США, кухонні шафи RTA і на замовлення; попередня система Fishbowl ERP) — https://webkul.com/blog/case-studies/how-best-online-cabinets-transformed-their-business-with-odoo-and-webkul/amp/ (S).
- **Azkatech**: кейс Kitwood (Ліван, кухні й шафи) — https://www.odoo.com/tr_TR/customers/industry/mesken-20/country/122 (S).
- **SilentInfotech, Biztech, Infintor, Aglowid**: сторінки/кейси «Odoo для меблів/кухонних шаф» (https://silentinfotech.com/case-study/custom-kitchen-cabinet-manufacturing-with-odoo-erp — 403 при читанні; https://www.biztechcs.com/services/odoo-erp-for-furniture, https://www.infintor.com/odoo-manufacturing-erp-for-furniture-industry/, https://aglowiditsolutions.com/case-studies/odoo-woodworking-erp-software/ — лише S) — змісту не перевірено [не перевірено].
- **Україна**: серед партнерів/інтеграторів у видачі — UBM Soft (https://www.odoo.com/partners/ubm-soft-10086935), ERP Ukraine LLC (https://www.odoo.com/partners/erp-ukraine-llc-6677724), KitWorks, Netframe, Solvve (S). **Жодного українського партнера з підтвердженим меблевим кейсом не знайдено.** Plugit (згаданий у R1): кейсу Odoo+Україна+меблі у видачі не знайдено [не перевірено].

### 2.5. Клієнтські історії на odoo.com (маркетинг Odoo, S/F)

- **Mintjens Meubels (Бельгія, ~70+ співробітників, на замовлення шафи/меблі)**: додатки — Inventory, Accounting, HR, Helpdesk, CRM, Manufacturing; BoM створюється в Odoo після технічних кресленів; CNC-ПЗ і автоматизоване складування плит «тісно інтегровані з Odoo inventory» (як — не описано); «кастомізацій менше 10%»; штрих-код на кожен виріб. Партнер не названий; Odoo.sh. Це маркетинг Odoo, цифри без розкриття. https://www.odoo.com/blog/customer-reviews-6/mintjens-meubels-maatkasten-transforming-furniture-with-tradition-and-innovation-1320 (F).
- **La Source (мікропилорама)**: гібрид Odoo + зовнішній калькулятор технічних даних; додатки не названі. https://www.odoo.com/customers/la-source-micro-scierie-locale-19955323 (F).
- Інші: Woodio (Фінляндія, SprintIT), TRU180, Kabnoury Furniture — лише S; деталі не читались.

### 2.6. Знахідки за підсегментами

| Підсегмент | Що знайдено в екосистемі | Прогалина |
|---|---|---|
| (а) корпусні/кухні на замовлення | Odoo `custom_furniture`/`carpenter`; конфігуратори (Pokutsoft, ec_cpq, ECOSIRE); розкрій MI ERP (19.0), LaserCAM (CNC); Winner Design→Odoo (Callista) | немає перевіреного кінця-в-кінець: замір → дизайн → розкрій з кромкою/текстурою → присадка/ЧПУ → монтаж; жоден модуль не підтверджено в продуктивній експлуатації |
| (б) серійні на склад/маркетплейси | лише стандарт (BoM, MRP, eCommerce); Doodex заявляє 5000+ SKU (маркетинг) | інтеграції з українськими маркетплейсами не шукались у цьому розділі [не перевірено] |
| (в) м'які | ECOSIRE configurator (приклад дивана), `textile_management` (Cybrosys, 19.0, деталі не читались), `ma_pos_cutting` (POS, не те) | розкрій тканини/шаблони, облік рулонів, каркас+оббивка — немає підтверджених |
| (г) масив/столярка | `carpenter` (Odoo/ECOSIRE), La Source (пилорама) | облік деревини за кубатурою/сортом/вологістю [не перевірено]; сушіння згадане лише в кейсі La Source |
| (д) офісні/контрактні | Project + Field Service + Planning у `custom_furniture` | тендерні процеси (Prozorro), специфікації, ТЕО — не знайдено |

---

## 3. Інтеграції Odoo з CAD/CAM меблів і ЧПУ

**Загальний висновок: готового підтвердженого коннектора Odoo до PRO100, imos iX, Cabinet Vision, Polyboard, WoodWOP, Biesse/Homag/SCM, Базис-Мебельщик не знайдено** у відкритих джерелах цієї перевірки. Відсутність у пошуку ≠ відсутність у світі [не перевірено].

| Система | Що знайдено | Статус |
|---|---|---|
| imos iX / iX CAM (Biesse) | iX CAM автоматично генерує програми ЧПУ «для всіх поширених виробників»; сумісність з ПЗ Biesse (B_SOLID, B_NEST, B_OPTI). Публічного коннектора imos–Odoo немає | https://www.imos3d.com/en/products/manufacturing-assembly/cnc-programming-ix-cam, https://biesse.com/ww/en/software/ix-by-imos (S). Інтеграція ймовірно кастомна (файловий обмін/API) [не підтверджено] |
| PRO100 | нічого про Odoo | не знайдено |
| Cabinet Vision (EzyNest) | лише твердження Doodex «підключаємо» | маркетинг, per-project |
| Polyboard / OptiNest (Homag-ланцюг) | Polyboard генерує .mpr для woodWOP; OptiNest виводить DXF; Odoo в ланцюжку немає | S (https://wooddesigner.org/homag-weeke-integration-polyboard/) |
| Winner Design (Callista) | **є** конектор Winner Design → Odoo, робота зверху вниз: композиція з пакета креслень передається в Odoo | F (Callista); версія Odoo не вказана |
| 2020KD / 2020 Design | згадка VentorTech; кастомний конектор, у сторі не опублікований; чи це той самий продукт, що 2020 Spaces — не підтверджено | S |
| Базис-Мебельщик, Bazis, Pytha, Planit | нічого про Odoo | не знайдено |
| SolidWorks (+PDM) | add-in CustomTools синхронізує продукти/BoM/документи з Odoo (remote calls), поле-рівневе «майстер-система», захист рядків, що існують лише в Odoo; виступ ATROFT на Odoo Experience 2025 | S/F-переказ: https://oduist.com/blog/odoo-experience-2025-ai-summaries-2/234-from-design-to-business-the-power-of-cad-pdm-plm-and-odoo-integration-236; не меблевий CAD, але патерн «CAD→BoM» |
| OpenBOM | **одностороння** інтеграція OpenBOM → Odoo: створює BoM, надсилає мініатюри, властивості, PDF/STEP/DXF у Odoo Documents; вимагає публічно доступний Odoo, Manufacturing, API-ключ; версії Odoo не вказані; з v16 підтримуються API-ключі (працюють у Community через JSON-RPC) | F: https://help.openbom.com/my-openbom/openbom-integration-for-odoo-help-documentation/ |
| Імпорт/експорт BoM з Excel | модулі `odoo_import_export_bom` (18.0), OCA `mrp_bom_structure_xlsx` — файловий міст | S: https://apps.odoo.com/apps/modules/18.0/odoo_import_export_bom |
| LaserCAM | див. §2.2; nesting+CNC-фреза | F |
| ЧПУ-верстати (Biesse/Homag/SCM) | прямого конектора Odoo/IoT Box/OPC UA не знайдено; типовий патерн — CAM/nesting публікує результат у Odoo через API (XML-RPC/JSON-RPC), G-code/MPR генерує CAM; Odoo як MES для верстата — не підтверджено | S (https://ecosire.com/apps/odoo/odoo-metal-fabrication-manufacturing, Doodex); Plataine WoodOptimizer/ProNest згадані як приклади ERP-ready nesting (не Odoo) |
| Форумна нитка «Industrial machineries integration with Odoo 14» | запит без підтвердженого рішення | S |

Типові патерни (з джерел): (1) CAD/CAM → файл (CSV/XLSX/DXF/MPR) → імпорт у BoM; (2) CAM → JSON-RPC → Odoo (потреби матеріалів, залишки, час різу); (3) Odoo як майстер складу і номенклатури, CAD — майстер геометрії; (4) розкрій як зовнішня система, Odoo приймає результат і веде залишки.

---

## 4. Висновки для рішення (тези, не факти)

1. Покриття «з коробки»: універсальне виробництво (BoM з варіантами, МО, операції, якість, субпідряд) є; специфічних меблевих функцій (розкрій з текстурою/кромкою, ділові залишки плит, розрахунок розмірів корпусних, присадка/ЧПУ, прив'язка до дизайн-ПЗ) у стандарті **не підтверджено**.
2. Ринок сторонніх модулів малий і неоднорідний: 1–3 модулі на нішу, переважно 2025–2026 років, без видимих рейтингів і кількості завантажень на сторінках; дві з трьох знайдених меблевих «пропозицій» — build-to-order послуги без публічних кейсів. Ризик: «модуль» може виявитись проєктом розробки.
3. Єдине підтверджене прямо меблеве ПЗ→Odoo — Winner Design (Бельгія), не для українського ринку.
4. Для україномовного ринку в екосистемі не виявлено меблевого рішення на Odoo з українською локалізацією податків (див. R1: `l10n_ua`, `l10n_ua_full`).

## 5. Відкриті питання (до людини / подальших кроків)

- Edition-матриця Odoo 19 (MRP/Shop Floor/PLM/Quality/Maintenance/Planning/FSM/Studio/MPS): звірити з таблицею на odoo.com/page/editions або порівнянням каталогів addons 19.0 і enterprise.
- Перегляд apps.odoo.com вручну за версіями 16–19 і ключовими словами (furniture, wood, cabinet, kitchen, joinery, panel, nesting, cutting, edge, upholstery) — повного переліку немає; рейтинг і завантаження зібрати зі сторінок вручну.
- Живі демо/trial для `mierp_cutting_optimizer`, `make_to_order_configurator`, `ec_cpq`; запит ECOSIRE на еталонного клієнта й зразок модуля.
- Чи існує imos/Cabinet Vision/Базис → Odoo у реальних проєктах (запит до вендорів і партнерів).
- Українські партнери Odoo: уточнити досвід меблевих проєктів (UBM Soft, ERP Ukraine, Solvve, KitWorks, Netframe).

---

## 6. R5: прохід по документації 19.0, вихідному коду й Apps Store (2026-11-11)

### 6.1. Документація Odoo 19.0 (F, прочитано напряму)

| Тема | Сторінка | Що підтверджено | Що лишилось |
|---|---|---|---|
| Передоплати в Sales | https://www.odoo.com/documentation/19.0/applications/sales/sales/invoicing/down_payment.html | Рахунок на передоплату: **відсоток** або **фіксована сума**; передоплата — не те саме, що умови оплати | — |
| Онлайн-підтвердження з оплатою | https://www.odoo.com/documentation/19.0/applications/sales/sales/sales_quotations/get_paid_to_validate.html | Клієнт у порталі натискає **Accept & Pay** і підтверджує замовлення оплатою | — |
| Умови оплати | https://www.odoo.com/documentation/19.0/applications/finance/accounting/customer_invoices/payment_terms.html | Умови оплати й **плани розстрочки** (оплата рахунку частинами) | — |
| Портал клієнта | https://www.odoo.com/documentation/19.0/applications/general/users/user_portals.html | Портал доступний за замовчуванням; клієнт **переглядає, завантажує й оплачує рахунки, зокрема часткові й передоплати**; доступ лише на читання | статус виробництва в порталі — не стандарт `[не перевірено]` |
| Field Service: worksheets | https://www.odoo.com/documentation/19.0/applications/services/field_service/worksheets.html | Робочі листи для виїзних задач (чекбокси, поля, файли, фото); шаблони, які проєктують у **Studio** | **Підпис клієнта** на сторінці не знайдено — `[не перевірено]` |
| Helpdesk: післяпродаж | https://www.odoo.com/documentation/19.0/applications/services/helpdesk/advanced/after_sales.html | Із тікета: **повернення коштів, купони, повернення товару (reverse transfer), ремонт, виїзд Field Service**; увімкнення може встановити додаткові модулі | — |
| Repairs | https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/repairs.html | Окремий додаток: ремонт пошкоджених повернених товарів | собівартість ремонту по замовленню — `[не перевірено]` |
| Мультивалютність | https://www.odoo.com/documentation/19.0/applications/finance/accounting/get_started/multi_currency.html | Валюти й курси (ручне й автоматичне оновлення) | перерахунок маржі відкритих замовлень за курсом — не стандарт (td_) |
| Maintenance | https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/maintenance.html | Облік обладнання й обслуговування | — |
| Фіскальні локалізації | https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations.html | «Ukraine» є у списку країн, але **без окремої сторінки документації** (на відміну від країн із посиланням) | — |

### 6.2. Редакції й ціна (F)

- **Сторінка цін українською** (https://www.odoo.com/uk_UA/pricing, 2026-11-11; **R6: цифри цього абзацу — помісячна оплата і ціни для відвідувача зі США, див. розбір нижче**): «Стандарт» — **US$ 38,90** за користувача на місяць, зі знижкою на перші 12 місяців US$ 31,10. «Індивідуальний» — **US$ 76,20** (зі знижкою US$ 61,00). **Light User — US$ 8,90**: як користувач — власні відпустки, витрати, відвідування, «My Planning», **Field Services**, **Inventory Barcode Operator**, Knowledge лише на читання; оформлюється через менеджера Odoo. Встановлення **Studio** або додавання компанії **автоматично переводить** на «Індивідуальний» план. Хостинг Odoo.sh — окремо.
- **R6: розбір цифр сторінки цін (HTML-код сторінки, 2026-11-11).** Перемикач «Річний / Помісячно» міняє класи `yearly_price` і `monthly_price`. Перекреслена ціна — це звичайна ціна, менша — знижка на перші 12 місяців («Знижка дійсна протягом 12 місяців для перших користувачів»).

  | План | Річна оплата: 1-й рік / далі | Помісячна оплата: 1-й рік / далі |
  |---|---|---|
  | «Стандарт» | US$ 24,90 / **31,10** | US$ 31,10 / **38,90** |
  | «Індивідуальний» | US$ 49,00 / **61,00** | US$ 61,10 / **76,20** |
  | Light User | US$ 8,90 (вираз у коді — `monthly_light`; річна ціна окремо не показана) | US$ 8,90 |

  Отже, R5 брав **помісячну** ціну (76,20) і порівнював її з **річними** тарифами Bimp. Варіант «На власному сервері» сторінка показує лише при річній оплаті.
- **R6: ціни залежать від країни відвідувача.** Сторінку віддано для `geoip_country_code: "US"` (поле в коді сторінки): середовище дослідження виходить в інтернет через США. Тобто це **ціни для США**, а не для України, хоча мова сторінки українська. Партнер Plugit (дата зміни сторінки 2026-10-05 — з метаданих HTML `article:modified_time` / `dateModified`, на сторінці не показана) публікує ціну ліцензії для України: «Стандарт» — €11,90 у перший рік і €14,90 далі, «Індивідуальний» — **€22,90 у перший рік і €27,90 далі, при річній оплаті** (https://plugit.com.ua/tarifs/). Ці цифри не суперечать odoo.com, якщо Odoo має окремі ціни для України `[не перевірено]`. Треба відкрити сторінку з української IP-адреси або запросити пропозицію в Odoo чи партнера (FUNCTIONAL-MAP §7, питання 10).
- **R6: Light User — що покриває (FAQ сторінки цін, англ.):** як користувач — власні відпустки, витрати, оцінювання, відвідування, рекомендації, **My Planning, Field Services, Inventory Barcode Operator**, Knowledge лише на читання; як працівник (запис співробітника без користувача) — розрахункові листки, **Point of Sale, Manufacturing Shop Floor**. Тобто монтажник (Field Service), комірник (Barcode) і робітник цеху (Shop Floor) — Light User. Обсяг прав Light User у Field Service (наприклад, підпис клієнта у звіті) у документації 19.0 `[не перевірено]`. Ліцензію оформлює радник Odoo: FAQ «How can I get a Light User license?» — зустріч із радником та **індивідуальна пропозиція** («customized quote»), тому US$ 8,90 — орієнтир, а не прайс (https://www.odoo.com/pricing, прочитано 2026-11-11, R7).
- **Офіційної таблиці Community / Enterprise за додатками** на сторінці цін немає. Непряме підтвердження з коду (6.3): `custom_furniture` залежить від `industry_fsm_report`, `planning`, `quality_control`, `mrp_workorder`, `account_followup`. Перевірено списком `addons/` гілки 19.0 публічного репозиторію `odoo/odoo` (Community, LGPL): **є** `mrp`, `project`, `sale_project`, `repair`, `maintenance`, `l10n_ua`; **немає** `planning`, `industry_fsm` (Field Service), `industry_fsm_report`, `quality`, `quality_control`, `mrp_workorder` (Shop Floor), `helpdesk`, `web_studio`, `account_followup`. Отже, Field Service, Planning, Quality, Shop Floor, Helpdesk і Studio — **лише Enterprise**, а Repairs і Maintenance є в Community (F, код). Це закриває питання R3 §1.3 для додатків пакета.

### 6.3. Що всередині `custom_furniture` 19.0 (F, вихідний код)

Джерело: публічний репозиторій `odoo/industry`, гілка 19.0, тека `custom_furniture` (https://github.com/odoo/industry/tree/19.0/custom_furniture), прочитано `__manifest__.py` і `data/*.xml`.

- **Залежності:** account_followup, calendar, crm, hr, industry_fsm_report, knowledge, mrp_workorder, planning, product_barcodelookup, purchase_stock, quality_control, quality_mrp, sale_project, sale_stock, sale_timesheet.
- **Увімкнені налаштування:** маршрути виробництва (routings), варіанти товарів, прайс-листи, шаблони пропозицій, **поповнення під замовлення (replenish on order = MTO)**, етапи проєктів, звіт про приймання MRP.
- **Дані:** 4 робочі центри (Assembly Area, Core Board Composing Machine, Quality Check Area, Sanding Area); 6 операцій (Cut Panels, Sanding panels, Structure Creation, Assemble legs, Final Sanding, Final verification); **1 атрибут «Color»**; 3 ролі планування (3D Designer, Architect, Installer); шаблон пропозиції «Interior Design Project»; проєкт «Customer Project Management» з задачами «Review Customer Technical Information → Project Configuration & measure → Bill of Material Configuration → Manufacture Order Creation → Final Invoice»; 2 контрольні точки якості (фото «Manufacture Verification», інструкція «Desk Plan», Pass/Fail «Stability testing»); демо-товар «Custom conference table».
- **Чого немає:** розмірів деталей, кромки, обрізків, імпорту з CAD, комплектації по місцях, акта монтажу, відрядної оплати, рекламацій, UA-інтеграцій.

**Висновок.** `custom_furniture` — демонстраційна конфігурація для **проєктних меблів (д) і інтер'єрних робіт**: конференц-стіл, архітектор, монтажник, задача «замір» у проєкті. Це **не** продукт для корпусного виробництва (а). Наш пакет може використовувати його як стартову конфігурацію, але меблева цінність — у td_. `carpenter` 19.0 залежить від base_industry_data, crm_enterprise, documents_hr, project_purchase, sale_mrp, sale_timesheet, stock_dropshipping.

### 6.4. Українська локалізація `l10n_ua` 19.0 (F, вихідний код)

`addons/l10n_ua` у `odoo/odoo` 19.0: «Ukraine - Accounting», автор ERP Ukraine, ліцензія LGPL-3, версія 1.4. Містить **лише план рахунків за П(С)БО, податки й групи податків** (`account.account-ua_psbo.csv`, `account.tax-ua_psbo.csv`) і українські переклади. **Податкової накладної, ЄРПН, звітності ДПС у модулі немає.** Їх закривають сторонні модулі (6.5) або облік лишається в BAS чи M.E.Doc (H-12).

### 6.5. Українські інтеграції в Odoo Apps Store для 19.0 (F, apps.odoo.com, 2026-11-11)

| Потреба | Модуль (технічна назва) | Автор | Ціна на сторінці |
|---|---|---|---|
| Нова Пошта | `bjet_nova_post` | BJET | $220,00 |
| Нова Пошта | `mobius_nova_poshta` | Mobius ERP | $334,95 |
| Нова Пошта | `nf_delivery_nova_poshta` | Netframe | $295,87 |
| НП + LiqPay + замовлення Prom.ua і Rozetka | `mdv_ukraine_commerce` | Modvanta | $39,90 |
| Checkbox (ПРРО) | `kw_checkbox` | Kitworks Systems | $279,13 |
| Checkbox для POS | `us_prro_checkbox` | UnitSoft | $279,13 |
| Checkbox для POS, рахунків і онлайн-оплат | `mdv_ua_checkbox_prro` | Modvanta | $64,84 |
| Приват24 для бізнесу: виписки | `bjet_privatbank_autoclient_statement_import` | BJET | $153,69 |
| ПриватБанк (Enterprise) | `nf_privatbank_integration_ee` | Netframe | $167,48 |
| Монобанк і Приват24: виписки | `mdv_ua_bank_sync` | Modvanta | $39,90 |
| Монобанк: виписки | `bjet_monobank_statement_import` | BJET | $153,69 |
| Монобанк: платежі (корпоративний API) | `l10n_ua_bank_mono_payment` | Svyatoslav Nadozirny | ціни на сторінці не знайдено (LGPL-3) |
| ЕДО «Вчасно» | `l10n_ua_edo_vchasno` | Svyatoslav Nadozirny | ціни не знайдено (LGPL-3) |
| ЕДО «Вчасно» | `vchasno_connect` | Implementation practice | $199,85 |
| M.E.Doc: експорт XML | `l10n_ua_medoc_export` | Svyatoslav Nadozirny | ціни не знайдено (LGPL-3) |
| Вчасно.Каса (ПРРО) | `us_prro_vchasno_kasa` | UnitSoft | не зчитано |

Сторінки модулів: `https://apps.odoo.com/apps/modules/19.0/<технічна назва>`. **Дату останнього оновлення й кількість завантажень зчитати не вдалося**: на сторінках вони підвантажуються динамічно. Якість модулів не перевірялась.

**Висновок.** Гігієна H-08–H-10 **закривається сторонніми модулями для 19.0** від кількох незалежних авторів (BJET, Modvanta, Netframe, UnitSoft, Kitworks, Svyatoslav Nadozirny). Ризик R-5 «локалізацію не перевірено» знижено: модулі існують, перевірити треба якість і підтримку (тест-встановлення на A-12). ПН/ЄРПН у стандарті немає. Експорт у M.E.Doc і ЕДО «Вчасно» — сторонні модулі.

### 6.6. Частка покриття стандартом (розрахунок, а не оцінка)

Метод: рядки функціональної карти (FUNCTIONAL-MAP §2, 49 рядків після R5) розкладено на три групи. **Стд/Налашт, підтверджено** — функцію повністю закриває стандарт, і це підтверджує документація 19.0 (OE:§1.1, §6.1) або код `custom_furniture`. **Стд як основа + td_/Інтегр** — стандарт дає основу, але потрібен модуль чи інтеграція. **td_/Інтегр** — стандарт не закриває. Результат: повністю стандарт (підтверджено) — 12 рядків (24 %); стандарт без перевірки — 3 (6 %); стандарт як основа + td_/інтеграція — 22 (45 %); лише td_/інтеграція — 12 (24 %). Перелік рядків — FUNCTIONAL-MAP §2.4. Оцінка R3–S «60–70 % стандартом» знята як нерозрахована.
