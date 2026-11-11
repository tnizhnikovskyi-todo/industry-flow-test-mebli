# R3. Екосистема Odoo для меблевого виробництва (Україна, КВЕД 31)

Дата перевірки джерел: 2026-11-11. **R10 (2026-11-11): аналітика в коді CE 19.0 (§7.1), задача проєкту в CE — лише дедлайн, без Ганта (§7.2), виняток зі «спільних моделей» і склад EE-мостів (§7.5).** **R8 (2026-11-11): пакет робимо одночасно для Community 19 і Enterprise 19 — порівняння редакцій, OCA 19.0 і td_ для CE — §7.** Методика: відкриті джерела (WebSearch/WebFetch). Вміст сторінок вважався даними; вбудованих інструкцій не виявлено.

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

> **R8: розділ застарів.** Таблицю редакцій розібрано з живої сторінки й звірено з кодом — §7.1–7.2; робоча гіпотеза нижче підтвердилась (Repairs і Maintenance — CE; Field Service, Planning, Quality, Shop Floor, PLM, Helpdesk, Studio, Sign, Documents, Barcode, Accounting — EE).

**Не підтверджено офіційно (R3).** Спроба відкрити https://www.odoo.com/page/editions (F): таблиця перелічує MRP (Shopfloor, Control Panel, Scheduling), PLM, Quality, Maintenance (розділ Supply Chain), Planning, Field Service (Services), Studio (Customization), але позначки Community/Enterprise у вилучений текст не потрапили. MPS на сторінці не згадується.

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

- ~~Edition-матриця Odoo 19~~ — **R8: закрито** (§7.1–7.2).
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

Метод: рядки функціональної карти (FUNCTIONAL-MAP §2, 49 рядків після R5) розкладено на три групи. **Стд/Налашт, підтверджено** — функцію повністю закриває стандарт, і це підтверджує документація 19.0 (OE:§1.1, §6.1) або код `custom_furniture`. **Стд як основа + td_/Інтегр** — стандарт дає основу, але потрібен модуль чи інтеграція. **td_/Інтегр** — стандарт не закриває. Результат: повністю стандарт (підтверджено) — 12 рядків (24 %); стандарт без перевірки — 3 (6 %); стандарт як основа + td_/інтеграція — 22 (45 %); лише td_/інтеграція — 12 (24 %). Перелік рядків — FUNCTIONAL-MAP §2.4. Оцінка R3–S «60–70 % стандартом» знята як нерозрахована. **R8:** це розрахунок для Enterprise; для Community покриття рахуємо окремо (FUNCTIONAL-MAP §2.4; відмінності по рядках — §7.4).

---

## 7. R8: пакет одночасно для Community 19 і Enterprise 19 (2026-11-11)

**Рішення власника (2026-11-11):** пакет робимо **одночасно для Odoo 19 Community (CE) і Enterprise (EE)**. **Ядро** — усі екрани MVP і наскрізний сценарій «кухня від заміру до рекламації» — мусить працювати на CE. На EE пакет використовує EE-додатки (Field Service, Shop Floor / `mrp_workorder`, Helpdesk, Quality, Sign, Planning, Documents, Studio тощо) як **підсилення або альтернативну реалізацію**, а не як залежність ядра. `custom_furniture` (EE) — лише джерело ідей і даних для EE-варіанта (FUNCTIONAL-MAP §7 п. 4).

Цей розділ замінює гіпотезу §1.3 і доповнює §6.2. Позначки достовірності — як у §0. Код читали `git clone --depth 1` гілок 19.0 (`odoo/odoo` — коміт `40e9be2b`, 2026-11-10; репозиторії OCA — дата останнього коміту в таблиці 7.3); маніфести читали скриптом, без установки модулів. **Жоден модуль OCA не встановлювали й не тестували** — статус нижче означає «модуль є в гілці 19.0 і позначений installable», а не «працює».

### 7.1. Офіційна таблиця редакцій (F)

Джерело: https://www.odoo.com/page/editions (HTML сторінки, прочитано 2026-11-11; у R3 позначки не зчитались, у R8 розібрано іконки `fa-check` / `fa-times` у двох колонках Community / Enterprise). Рядки, важливі для пакета:

| Додаток (як на сторінці) | CE | EE |
|---|---|---|
| Invoicing, Payments, Expenses | ✓ | ✓ |
| Accounting (повний облік, звіти, консолідація, локалізації) | ✗ | ✓ |
| Documents, Spreadsheet, Sign | ✗ | ✓ |
| CRM, Sales, Point of Sale, Website, eCommerce, Live Chat | ✓ | ✓ |
| Subscriptions, Rental | ✗ | ✓ |
| Inventory | ✓ | ✓ |
| ↳ Barcode | ✗ | ✓ |
| Manufacturing (MRP) | ✓ | ✓ |
| ↳ Shopfloor, Control Panel, Scheduling | ✗ | ✓ |
| PLM, Quality | ✗ | ✓ |
| Purchase, Maintenance | ✓ | ✓ |
| Employees, Time Off, Fleet, Surveys, Calendar, Discuss, To-Do | ✓ | ✓ |
| Project, Timesheet | ✓ | ✓ |
| ↳ Timesheet: grid view, timer, reminders, validation | ✗ | ✓ |
| Field Service, Helpdesk, Planning, Appointments | ✗ | ✓ |
| Approvals, VoIP, IoT, Knowledge, Marketing Automation | ✗ | ✓ |
| Studio | ✗ | ✓ |
| ↳ Comprehensive Accounting: General Ledger, Bank Statement Reconciliation, Analytic Accounting, Budgets, Consolidation, Localizations, Reports (R9) | ✗ | ✓ |
| Version Upgrades (R9) | ✗ | ✓ |
| Hosting (R9) | ✗ | ✓ |
| User interface: Desktop • Web Browser (R9) | ✓ | ✓ |
| User interface: Mobile • Android and iOS (R9) | ✗ | ✓ |

**Repairs** у таблиці не названо, але `addons/repair` (LGPL-3) є в CE 19.0 (§6.2, F, код). Таблиця збігається з перевіркою кодом у §6.2.

**R9 (2026-11-11; та сама сторінка, розбір рядків `<tr>`: `fa-close` — ✗, `fa-check` — ✓).** У R8 пропущено рядки «Comprehensive Accounting», «Version Upgrades», «Hosting» і «Mobile». Наслідки для пакета:
1. **Облік.** Рядок «Comprehensive Accounting» (General Ledger, звірка виписок, Analytic Accounting, бюджети, консолідація, звіти) — ✗ для CE як **пакет звітів та інструментів обліку**. **R10 (код CE 19.0, прочитано 2026-11-11): модель і подання аналітики в CE є.** `account` залежить від `analytic` і постачає подання аналітичних планів, рахунків, моделей розподілу й рядків (`views/account_analytic_plan_views.xml`, `account_analytic_account_views.xml`, `account_analytic_distribution_model_views.xml`, `account_analytic_line_views.xml` — https://raw.githubusercontent.com/odoo/odoo/19.0/addons/account/__manifest__.py); `stock_account` дає руху запасу поле `analytic_account_line_ids` (https://raw.githubusercontent.com/odoo/odoo/19.0/addons/stock_account/models/stock_move.py, рядок 50); `mrp_account` дає робочому замовленню `mo_analytic_account_line_ids` і `wc_analytic_account_line_ids` (https://raw.githubusercontent.com/odoo/odoo/19.0/addons/mrp_account/models/mrp_workorder.py, рядки 10–11) і підписує ці рядки назвою МО (https://raw.githubusercontent.com/odoo/odoo/19.0/addons/mrp_account/models/mrp_production.py, рядки 31–34). R9 помилково подавав аналітичні рахунки як «лише EE». **У CE немає звітів та інструментів обліку:** General Ledger і фінзвітів, віджета звірки виписок, бюджетів `[назви EE-модулів не перевірено: код закритий]`. Чи видно меню аналітики в CE без EE і чи потрапляють рядки з МО на аналітичний рахунок замовлення — `[підтвердити установкою в перевірці до A-21, FUNCTIONAL-MAP §3.4 п. 14]`. Це зачіпає P-12 (розподіл витрат), H-06 (екран 13 «собівартість замовлення»), H-08 (звірка оплат) і модулі імпорту виписок UA-банків, чия залежність від EE-модуля імпорту на CE не перевірена (§7.6).
2. **Оновлення версії** від Odoo — лише EE. На CE — OpenUpgrade або ручна міграція (§7.8).
3. **Мобільного застосунку Odoo на CE немає.** Польові екрани CE — веб-клієнт у браузері телефону або планшета + OCA `web_responsive` (LGPL-3) `[не перевірено на телефоні/планшеті]` (§7.8).

### 7.2. Склад CE 19.0 за кодом (F)

Список `addons/` гілки 19.0 `odoo/odoo` (коміт `40e9be2b`, 2026-11-10; https://github.com/odoo/odoo/tree/19.0/addons):

- **Є в CE:** `sale`, `sale_management` (шаблони пропозицій), `sale_stock`, `sale_mrp`, `sale_project`, `sale_timesheet`, `crm`, `purchase_stock`, `stock`, `stock_account`, `stock_picking_batch`, `stock_dropshipping`, `stock_landed_costs`, `mrp`, `mrp_account`, `mrp_subcontracting`, `mrp_subcontracting_account`, `mrp_repair`, `mrp_landed_costs`, `repair`, `maintenance`, `project`, `project_mrp`, `project_purchase`, `project_todo`, `hr_timesheet`, `hr_attendance`, `hr_expense`, `hr_skills`, `calendar`, `portal`, `payment`, `website`, `website_sale`, `website_payment`, `point_of_sale`, `sale_pdf_quote_builder`, `product_matrix`, `barcodes`, `base_automation`, `spreadsheet_dashboard`, `l10n_ua`.
- **Немає в CE (це EE):** `planning`, `industry_fsm`, `industry_fsm_report`, `quality`, `quality_control`, `mrp_workorder` (Shop Floor), `mrp_plm`, `mrp_mps`, `helpdesk`, `web_studio`, `sign`, `documents`, `knowledge`, `stock_barcode`, `account_accountant`, `account_followup`, `appointment`, `currency_rate_live` (автоматичне оновлення курсів).
- **Що CE `mrp` дає для цеху (F, код):** на робочому замовленні є кнопки **Start / Pause / Done** (`button_start`, `button_pending`, `button_finish` у `mrp/views/mrp_workorder_views.xml`), облік часу (`time_ids`, модель продуктивності робочого центру), **блокування робочого центру з причиною** (`button_block`, модель `mrp.workcenter.productivity.loss`), **планування робочих замовлень за календарем робочих центрів** (`button_plan` / `_plan_workorders` у `mrp_production.py`) і поле **OEE** робочого центру. Окремого цехового інтерфейсу (Shop Floor), Ганта (`Scheduling`) і MPS у CE немає.
- **На кого пишеться час у CE (F, код; R9):** запис продуктивності `mrp.workcenter.productivity` у CE 19.0 має поле `user_id` — користувач Odoo (https://github.com/odoo/odoo/blob/19.0/addons/mrp/models/mrp_workcenter.py, рядок 531, прочитано 2026-11-11). Поля працівника в цій моделі CE немає. Робота «як працівник без користувача» — можливість EE Shop Floor (FAQ Light User, https://www.odoo.com/pricing; FUNCTIONAL-MAP §3.2). Отже, на CE кожен робітник цеху — або користувач Odoo, або td_-планшет сам веде ідентифікацію працівника (PIN чи бейдж) і пише час на працівника. Це входить у P-04 (планшет) і H-07 (відрядна).
- **Задача проєкту в CE (F, код; R10):** `project.task` у CE 19.0 має `date_deadline` і `date_end`, але `date_end` — дата закриття (ставиться методом `update_date_end` при переході в згорнуту стадію), а не плановий кінець; полів планових початку й кінця (`planned_date_begin`) у CE-моделі немає. Календар задач побудований на `<calendar date_start="date_deadline" …>` (https://raw.githubusercontent.com/odoo/odoo/19.0/addons/project/models/project_task.py, рядки 180–183; https://raw.githubusercontent.com/odoo/odoo/19.0/addons/project/views/project_task_views.xml, рядок 829; прочитано 2026-11-11). Подання Gantt у CE немає. Наслідки: (1) td_ додає власні поля початку й кінця виїзду та ресурс «бригада» (екран 10, P-10); (2) на EE поля планування задач дає EE-модуль проєкту `[назву EE-поля й модуля перевірити установкою: код закритий]` — EE-міст зіставляє td_-поля з ними (§7.5); (3) P-03 на CE базово — календар, список або зведена таблиця завантаження, **без Ганта**; Гант — лише OCA `web_timeline` (AGPL-3, варіант (а)) або власний JS-вид (години `[не пораховано]`).
- **Підпис клієнта в CE (F, документація):** Sales дає **онлайн-підпис** для підтвердження замовлення в порталі (https://www.odoo.com/documentation/19.0/applications/sales/sales/sales_quotations/get_signature_to_validate.html, прочитано 2026-11-11). Це механізм підпису порталу; акт монтажу на ньому — td_ `[придатність для акта не перевірено]`.
- **Field Service worksheets на EE (F, документація):** «Worksheet templates are designed using Studio. Enabling the Worksheets feature automatically installs the Studio app, which may impact your price plan» (https://www.odoo.com/documentation/19.0/applications/services/field_service/worksheets.html, прочитано 2026-11-11). Отже, замір-лист через worksheet на EE вмикає Studio і план «Індивідуальний»; за правилом R-3 td_ на Studio не будуємо — **замір-лист — td_ на обох редакціях**.

### 7.3. OCA для 19.0: що закриває EE-прогалини на CE (F, код гілок 19.0)

Перевірено `git ls-remote` і клоном гілки `19.0` (https://github.com/OCA/<репозиторій>/tree/19.0). «Статус» — поле `development_status` маніфесту; «не вказано» — поля немає. **R9:** колонка «Ліцензія» — поле `license` маніфестів гілки 19.0 (raw.githubusercontent.com/OCA/<репозиторій>/19.0/<модуль>/__manifest__.py, прочитано 2026-11-11); перелік і висновки — §7.8. **Не встановлювали й не тестували.**

| EE-додаток | Репозиторій OCA (коміт гілки 19.0) | Модулі в 19.0 (installable) | Статус | Що лишається td_ на CE | Ліцензія (маніфест 19.0, R9) |
|---|---|---|---|---|---|
| Field Service | `field-service` (2026-11-06) | 34 модулі: `fieldservice` 19.0.1.2.3, `fieldservice_sale`, `fieldservice_stock`, `fieldservice_calendar`, `fieldservice_route`, `fieldservice_repair`, `fieldservice_sign`, `fieldservice_portal`, `fieldservice_project`, `fieldservice_timeline` та ін. | `fieldservice` — Production/Stable; більшість інших — Beta; `fieldservice_portal` — не вказано | замір-лист, акт монтажу, % бригаді (як і на EE) | AGPL-3 (`fieldservice`, `_sale`, `_calendar`, `_route`, `_sign`, `_project`) |
| Helpdesk | `helpdesk` (2026-11-11) | 18 модулів: `helpdesk_mgmt` 19.0.1.3.2, `helpdesk_mgmt_sale`, `helpdesk_mgmt_project`, `helpdesk_mgmt_fieldservice`, `helpdesk_mgmt_sla`, `helpdesk_type`, `helpdesk_product` | `helpdesk_mgmt`, `_sale`, `_project` — Production/Stable; `_sla`, `_fieldservice` — не вказано | «повернення / ремонт / виїзд із тікета» (на EE — стандарт after-sales, §6.1) + рекламація до деталі | AGPL-3 (`helpdesk_mgmt`, `_sale`, `_fieldservice`) |
| Quality | `manufacture` (2026-11-03) | `quality_control_oca` 19.0.1.0.0 (залежить лише від `product`); модуля контролю на МО (`quality_control_mrp_oca` у попередніх версіях) у 19.0 **немає**. Також `management-system`: `mgmtsystem_nonconformity`, `mgmtsystem_quality` | не вказано | зв'язка точки контролю з МО й операцією, фото | AGPL-3 (`quality_control_oca`, `mgmtsystem_nonconformity`) |
| Shop Floor | `manufacture` | `mrp_progress_button`, `mrp_workorder_sequence` (Beta); окремого цехового інтерфейсу немає | не вказано / Beta | «планшет цеху» на стандартних кнопках CE (7.2) | `mrp_progress_button` — AGPL-3; `mrp_workorder_sequence` — LGPL-3 |
| Planning, Scheduling (Гант) | `web`, `calendar`, `project`, `manufacture` | `web_timeline` 19.0.1.0.1 (Production/Stable), `resource_booking` (Production/Stable), `project_timeline`, `mrp_multi_level` (Production/Stable) | див. колонку | подання графіка бригад і дільниць (налаштування) | `web_timeline`, `resource_booking`, `project_timeline` — AGPL-3; `mrp_multi_level` — LGPL-3 |
| PLM (ECO) | `sale-workflow` (2026-11-10) | `sale_order_revision` (версії замовлення); ECO для BoM — немає | не вказано | версія специфікації замовлення (P-16) | AGPL-3 (`sale_order_revision`) |
| Sign | `sign` (2026-11-11) | `sign_oca` 19.0.1.0.0; міст `fieldservice_sign` | не вказано / Beta | підпис акта (або підпис порталу CE, 7.2) | AGPL-3 (`sign_oca`, `fieldservice_sign`) |
| Documents | `dms` (2026-11-11) | `dms` 19.0.1.1.7 | не вказано | — (не в MVP) | LGPL-3 (`dms`) |
| Knowledge | `knowledge` (2026-11-11) | `document_page` і 7 похідних | не вказано | — (не в MVP) | AGPL-3 (`document_page`) |
| Barcode | `stock-logistics-barcode` (2026-10-26) | лише `barcodes_generator_abstract`, `barcodes_generator_product`, `product_multi_barcode`; модуля сканування операцій складу (`stock_barcodes` у попередніх версіях) у 19.0 **немає** | не вказано | екран сканування комплектації (D-04), етикетки деталей (P-09) | `product_multi_barcode` — AGPL-3; решта не перевіряли |
| Accounting (повний) | `account-financial-reporting`, `account-reconcile`, `account-financial-tools`, `mis-builder` (усі 2026-11-11) | `account_financial_report`, `account_tax_balance` (Mature), `account_reconcile_oca`, `account_statement_base` (Mature), `account_asset_management` (Mature), `account_fiscal_year` (Production/Stable); гілка `mis-builder` 19.0 існує, модулі не перелічували | різний | залежить від рішення №5 (облік в Odoo чи в BAS/BAF) | `account_financial_report`, `account_reconcile_oca`, `account_tax_balance` — AGPL-3; `account_statement_base` — LGPL-3; решта не перевіряли |
| `account_followup` (нагадування про оплату) | `credit-control` (2026-11-11) | `account_credit_control`, `account_invoice_overdue_warn`, `sale_financial_risk` | не вказано | правило «доплата до монтажу» (H-08) — td_ на обох редакціях | AGPL-3 (`account_credit_control`, `account_invoice_overdue_warn`, `sale_financial_risk`) |
| `currency_rate_live` | `currency` (2026-11-11) | `currency_rate_update` — у 19.0 лише провайдер **ECB**; провайдера НБУ немає | не вказано | курс НБУ (D-14) — малий td_ | AGPL-3 (`currency_rate_update`) |
| Appointments (запис на замір) | `calendar` | `resource_booking` (Production/Stable) | — | налаштування | AGPL-3 (`resource_booking`) |
| Studio | — | замінника немає; td_ не будуємо на Studio на жодній редакції (R-3) | — | — | — |
| Підтримка, тема UI EE | `web` | `web_responsive` (Production/Stable) — адаптивний інтерфейс CE | — | — | **LGPL-3** (`web_responsive`) |

**R9: що з ліцензій випливає.** Усі модулі OCA, які R8 брав для ядра CE (виїзди, тікети, контроль якості, Гант, запис, підпис, нагадування, версії замовлення, курси), — **AGPL-3**; LGPL-3 — лише `web_responsive`, `mrp_multi_level`, `mrp_workorder_sequence`, `dms`, `account_statement_base`. Тому базовий варіант ядра (§7.5) не залежить від AGPL-модулів; наслідки для ліцензії td_ — §7.8 `[не перевірено юристом]`.

**Порожні гілки 19.0 (F):** `OCA/product-configurator` і `OCA/l10n-ukraine` мають гілку 19.0, але в ній **немає жодного модуля** (лише службові файли; останній коміт обох — 2025-09-30). Тобто ні конфігуратора OCA, ні OCA-локалізації України для 19.0 немає. Для P-01 лишаються td_ або сторонні модулі (Pokutsoft `make_to_order_configurator` заявлено для «Community і Enterprise», §2.1, не перевірено).

### 7.4. Рядки функціональної карти: CE 19, EE 19, OCA, td_

Лише рядки, де основа — Odoo (рядки «лише td_ / Інтегр» без стандартної основи — H-09, H-12, P-01, P-09, D-01, D-09…D-13, D-16 — однакові на обох редакціях і тут не повторюються). ID — FUNCTIONAL-MAP §2.

| Рядок | Enterprise 19 дає | Community 19 дає | OCA 19.0 для CE | td_ на CE (понад td_ на EE) |
|---|---|---|---|---|
| H-01 калькуляція | Sales, вартість BoM | те саме (`sale`, `mrp_account`) | — | — |
| H-02 специфікація | багаторівнева BoM | те саме (`mrp`) | `mrp_bom_hierarchy` | — |
| H-04 МО з замовлення | MTO, робочі центри | те саме | — | — |
| H-06 собівартість | вартість МО, WIP; повний облік (Accounting) | вартість МО (`mrp_account`, `stock_account`); аналітика в коді CE є, `mrp_account` пише аналітичні рядки з МО (R10, §7.1) — `[підтвердити установкою]`; звітів та інструментів Accounting у CE немає; WIP-проводки на CE `[не перевірено]` | `account_financial_report` (AGPL-3, необов'язково) | звіт по замовленню — як на EE |
| H-07 відрядна | облік часу Shop Floor (працівник без користувача) | облік часу робочих замовлень (`time_ids`, CE код) — **на користувача** (`user_id`), поля працівника немає (§7.2) | `hr_timesheet_*` | ідентифікація працівника (PIN / бейдж) — у складі td_-планшета (P-04) |
| H-08 оплати | передоплати, Accept & Pay, розстрочка; нагадування `account_followup` | передоплати, Accept & Pay, портал — CE; `account_followup` — немає | `account_credit_control` (AGPL-3) — лише необов'язковий адаптер | td_-правило «доплата до монтажу» без followup (S); звірка банківських виписок — у таблиці лише EE (§7.1) |
| H-10 локалізація | `l10n_ua` + Accounting | `l10n_ua` (LGPL) + Invoicing | `account_*` OCA; `l10n-ukraine` 19.0 порожній | облік — рішення №5 |
| H-11 дошка | етапи проєкту | те саме (`project`) | — | — |
| P-02 КП | шаблони пропозицій | те саме (`sale_management`) | — | — |
| P-03 планування | планування МО + Гант (Scheduling) + Planning | `button_plan` за календарем робочих центрів; Ганта немає — подання завантаження: календар, список, зведена таблиця (R10, §7.2) | `web_timeline` (AGPL-3, необов'язково), `mrp_multi_level` (LGPL-3) | td_ подання завантаження дільниць на стандартних поданнях CE (S–M; базовий варіант §7.5) |
| P-04 планшет | Shop Floor | кнопки Start / Pause / Done і блок із причиною на робочому замовленні; цехового інтерфейсу немає | `mrp_progress_button` (AGPL-3) | **планшет цеху з ідентифікацією працівника (PIN) (M)** |
| P-06 брак, ремонт | Scrap, Unbuild, Repairs | те саме | — | — |
| P-07 якість | Quality (контрольні точки на операціях, фото) | немає | `quality_control_oca` (AGPL-3, без зв'язки з МО) | **власні контрольні точки на МО з фото (M); поза MVP** |
| P-08 партії | лоти | те саме | — | — |
| P-10 монтаж і графік | Field Service + Planning | немає; є Project і Calendar (задача CE — лише дедлайн, календар на `date_deadline`, R10, §7.2) | `fieldservice` (+ `_sale`, `_calendar`, `_route`; AGPL-3) — запасний варіант | **графік бригад і статуси виїзду на задачах проєкту й календарі — td_ (S–M), базовий варіант §7.5** |
| P-11 сервіс із тікета | Helpdesk after-sales: повернення, ремонт, виїзд | Repairs; Helpdesk немає | `helpdesk_mgmt`, `_sale`, `_fieldservice` (AGPL-3) — не в ядрі: колізія `helpdesk.ticket` з EE (§7.5) | **td_-модель рекламації з діями «повернення / ремонт / виїзд» (M)** |
| P-12, P-13 аналітика, кілька юросіб | є; кілька компаній переводить на план «Індивідуальний» (§6.2) | аналітика: модель і подання в коді CE є (`analytic`, `account`, `mrp_account`; R10, §7.1) — `[підтвердити установкою]`; рядок «Comprehensive Accounting» таблиці — пакет звітів та інструментів обліку; мультикомпанія `[Стд?: документацію не читали]`, без доплати | — | — |
| P-14 MTO / MTS | є | те саме | — | — |
| P-15 сайт, POS | Website, POS | те саме | — | інтеграції — однаково |
| P-16 change order | PLM ECO | PLM немає | `sale_order_revision` (AGPL-3) — базово не беремо | **власна версія специфікації без ECO (M)** |
| P-17 вузькі місця | звіти Delays, OEE, Production analysis | поле OEE (CE код); звіти Delays і Production analysis на CE `[не перевірено]` | — | — |
| D-02 порізка-послуга | субпідряд | те саме (`mrp_subcontracting`) | `mrp_subcontracting_purchase_link` | — |
| D-03 замір | FSM worksheet (вмикає Studio) — не використовуємо; td_ | — | `fieldservice` (AGPL-3) — запасний; базово задачі проєкту (§7.5) | замір-лист — td_ **на обох** (7.2); мобільне подання на CE (§7.8) |
| D-04 комплектація | Barcode, пакування | пакування й пакетні переміщення; Barcode немає | `stock_barcodes` у 19.0 немає | **екран сканування комплектації (M)** |
| D-05 акт монтажу | FSM; підпис у звіті FSM `[не перевірено]`; Sign | підпис порталу (Sales) | `fieldservice_sign` + `sign_oca` (AGPL-3, необов'язково) | **підпис акта на підписі порталу CE (S–M)**; мобільне подання (§7.8) |
| D-06 рекламація | Helpdesk, Repairs (+ та сама td_-модель через міст) | Repairs | `helpdesk_mgmt` — не в ядрі (колізія з EE, §7.5) | **власна td_-модель рекламації на обох редакціях; на CE — без тікетів OCA (M)** |
| D-07, D-08 дати, портал | портал | те саме (`portal`) | — | — |
| D-14 курс | мультивалютність, `currency_rate_live` (провайдер НБУ `[не перевірено]`) | мультивалютність, ручні курси | `currency_rate_update` (AGPL-3, лише ECB) | **курс НБУ — власний td_-провайдер (S)** |
| D-15 партії | лоти | те саме | — | — |
| D-17 претензія | повернення постачальнику | те саме | — | — |
| X-01…X-03 (д) | Project, віхи, передоплати | те саме (`project`, `sale_project`) | `project_timeline` | — |

### 7.5. Базовий варіант ядра: моделі, спільні для CE і EE, без AGPL-залежностей (R9)

`[базовий варіант документа з R9; підтвердити на A-10 після перевірки FUNCTIONAL-MAP §3.4 п. 14]` R8 лишав вибір «OCA `fieldservice` чи задачі проєкту» на A-10, а години рахував за оптимістичною гілкою OCA. R9 фіксує один базовий варіант і перераховує під нього години (FUNCTIONAL-MAP §1.1) і покриття (§2.4).

**Замір і монтаж.** EE Field Service (`industry_fsm`) побудований на задачах проєкту, а OCA `fieldservice` має власну модель `fsm.order` (https://github.com/OCA/field-service/blob/19.0/fieldservice/models/fsm_order.py, прочитано 2026-11-11): колізії назв з EE немає, але на EE були б два паралельні «виїзні» додатки. **Базово:** замір, графік бригад, статуси виїзду й акт — td_ на **задачах проєкту й календарі**, які є в CE і EE; EE-міст вмикає для цих задач інтерфейс Field Service. OCA `fieldservice` — запасний варіант (а) (рішення №14 FUNCTIONAL-MAP §7).

**R10: виняток із «спільних моделей».** Модель задачі спільна, але поля планування — ні: на CE задача має лише дедлайн (§7.2), тож td_ додає поля інтервалу виїзду й бригаду; на EE ті самі задачі вже мають поля планування EE-модуля проєкту — міст зіставляє одне з одним, щоб на EE не було двох наборів дат `[назву EE-поля перевірити установкою]`.

**Рекламація (F, код).** OCA `helpdesk_mgmt` оголошує модель `_name = "helpdesk.ticket"` (https://github.com/OCA/helpdesk/blob/19.0/helpdesk_mgmt/models/helpdesk_ticket.py, рядок 6, прочитано 2026-11-11) — ту саму назву, що й модель EE-додатка `helpdesk` (код EE закритий; модель `helpdesk.ticket` видно в демо-даних `odoo/industry` 19.0, модуль якого залежить від `helpdesk`: https://github.com/odoo/industry/blob/19.0/bike_shop/demo/helpdesk_ticket.xml, прочитано 2026-11-11). Отже, спільна установка `helpdesk_mgmt` і EE Helpdesk на одній базі конфліктна `[не перевірено установкою]`. Якби екран 12 на CE стояв на `helpdesk_mgmt`, на EE це була б не «міст», а інша реалізація з міграцією даних тікетів. **Базово:** власна td_-модель рекламації на обох редакціях (на CE — без тікетів OCA); EE-міст пов'язує її з Helpdesk. На CE рядки D-06 і P-11 — M, а не S / S–M (FUNCTIONAL-MAP §2.4).

**Ліцензія.** Ядро td_ не залежить від AGPL-модулів OCA (§7.8). З OCA в ядрі — лише LGPL-3: `web_responsive` (мобільний UI), за потреби `mrp_multi_level`. AGPL-модулі — лише необов'язкові адаптери, які встановлюються окремо, якщо власник обере варіант (а).

**EE-мости** (тонкі модулі `td_*_ee`, встановлюються лише на EE) `[припущення щодо складу]`: Field Service (замір і акт у FSM), Shop Floor (планшет → `mrp_workorder`), Quality (контроль → `quality_control`), Helpdesk (рекламація → `helpdesk`), Sign (акт → Sign), Planning (графік бригад). Кожен міст — необов'язковий. **R10:** Barcode, `account_followup`, `currency_rate_live` і PLM (ECO) мостів не мають: на EE за замовчуванням працює td_ ядра (екран сканування, td_-правило доплати, td_-провайдер курсу НБУ, версія специфікації); ці EE-додатки клієнт вмикає за бажанням, td_-аналоги тоді вимикаються параметром пакета `[припущення щодо реалізації]` (FUNCTIONAL-MAP §2.4). Мости для них — альтернатива, +72–240 год (3–4 × 24–60) до накладних, у рамку не включено. Ядро CE має працювати на EE і без них — **за умови, що ядро не залежить від OCA-модулів із назвами моделей EE (`helpdesk_mgmt`) і на базі немає конфліктних додатків** `[не перевірено установкою]`.

### 7.6. Хостинг і вартість CE (F / [не перевірено])

- **Odoo Online не дає CE з власними модулями**, а **Odoo.sh — платформа для Enterprise**: на сторінці цін Odoo.sh «The hosting price does not include the enterprise licence» (https://www.odoo.sh/pricing), у FAQ — «Enterprise customers: You must subscribe to Odoo.sh, meaning your enterprise subscription has to include Odoo.sh» (https://www.odoo.sh/faq, обидві прочитано 2026-11-11). Ціни Odoo.sh сторінка рахує скриптом — **не зафіксовано** `[не перевірено]`. Розгортання CE на Odoo.sh `[не перевірено]`.
- **CE — власний сервер (VPS).** Публічні ціни, прочитано 2026-11-11: Hetzner Cloud — від **€5,49** на місяць без ПДВ (спільні vCPU), з виділеними vCPU — від **€36,99** (https://www.hetzner.com/cloud/); Hostinger KVM 2 (2 vCPU, 8 ГБ RAM) — **$14,99** на місяць після акційного періоду, KVM 4 (4 vCPU, 16 ГБ) — **$28,99**, KVM 8 (8 vCPU, 32 ГБ) — **$49,99** (https://www.hostinger.com/vps-hosting). Яка конфігурація потрібна для 10 / 25 / 50 користувачів Odoo 19 — `[не перевірено]`; українські хостинг-провайдери в R8 не відкрились (ukraine.com.ua — 429).
- **Ліцензії CE — 0** (LGPL-3), користувачі без обмежень і без поділу на Light User. Підтримку, оновлення безпеки й резервні копії CE виконує партнер — ставка 1 975–2 400 грн/год (Plugit, P3). Річний обсяг адміністрування — `[припущення]` (FUNCTIONAL-MAP §3.2, чутливість 24 / 48 / 96 год). **R9:** у CE-тариф не входять повний облік і сервіс оновлення версій (таблиця редакцій, §7.1; §7.8).
- **Українські модулі на CE (F, apps.odoo.com, 2026-11-11):** сумісність із **Community і Enterprise** прямо заявлено на сторінках `bjet_nova_post`, `mdv_ukraine_commerce`, `mdv_ua_checkbox_prro`, `bjet_privatbank_autoclient_statement_import`; `bjet_monobank_statement_import` — «Community and Enterprise 18» (19.0 є у версіях). `nf_privatbank_integration_ee` — для Enterprise (за назвою). Для решти модулів §6.5 сумісність із CE `[не перевірено]`; залежність модулів імпорту виписок від EE-модуля імпорту на CE `[не перевірено]`.

### 7.7. Що в R8 не перевірено

1. Жоден модуль OCA 19.0 не встановлено: якість, повнота міграції, сумісність між собою — `[не перевірено]` (тест-встановлення на A-12).
2. Звіти Delays і Production analysis у CE 19; WIP-проводки без Accounting; мультикомпанія й аналітика в CE — документацію не читали.
3. Підпис клієнта у звіті EE Field Service (як і в R5) і придатність підпису порталу CE для акта монтажу.
4. Ціни Odoo.sh; розмір VPS для 10–50 користувачів; українські VPS-провайдери.
5. Провайдер НБУ в EE `currency_rate_live`.
6. Сумісність із CE решти українських модулів §6.5.
7. **R9:** юридична оцінка AGPL-модулів OCA для ліцензії td_ і для поєднання з EE (§7.8).
8. **R9:** конфлікт `helpdesk_mgmt` з EE Helpdesk на одній базі — установкою.
9. **R9:** веб-клієнт CE з `web_responsive` на телефоні й планшеті: замір, фото з камери, підпис пальцем, слабкий зв'язок.
10. **R9→R10:** код аналітики в CE є (§7.1) — підтвердити установкою меню й рядки з МО; звірка виписок на CE; календар задач CE (лише дедлайн) для графіка бригад; td_-сканування й td_-правило доплати на EE-базі з Barcode і `account_followup`; покриття OpenUpgrade 19→20 для модулів пакета.

### 7.8. R9: ліцензії OCA, колізії моделей, оновлення версій, мобільний інтерфейс (2026-11-11)

**Ліцензії (F).** Поле `license` маніфестів гілок 19.0 (raw.githubusercontent.com/OCA/<репозиторій>/19.0/<модуль>/__manifest__.py, прочитано 2026-11-11):
- **AGPL-3:** `fieldservice`, `fieldservice_sale`, `fieldservice_calendar`, `fieldservice_route`, `fieldservice_sign`, `fieldservice_project`, `helpdesk_mgmt`, `helpdesk_mgmt_sale`, `helpdesk_mgmt_fieldservice`, `quality_control_oca`, `mgmtsystem_nonconformity`, `mrp_progress_button`, `web_timeline`, `resource_booking`, `project_timeline`, `sign_oca`, `sale_order_revision`, `account_credit_control`, `account_invoice_overdue_warn`, `sale_financial_risk`, `currency_rate_update`, `account_reconcile_oca`, `account_financial_report`, `account_tax_balance`, `product_multi_barcode`, `document_page`.
- **LGPL-3:** `web_responsive`, `mrp_multi_level`, `mrp_workorder_sequence`, `dms`, `account_statement_base`.
- **Odoo.** CE 19 — LGPL-3. Ліцензія EE дозволяє розповсюджувати модулі до EE «under the license of your choice, provided that it is compatible with the terms of the Odoo Enterprise Edition License (For example: LGPL, MIT, or proprietary licenses similar to this one)» і використовувати з EE модулі, «provided that their license is compatible with the terms of the Odoo Enterprise License» (https://www.odoo.com/documentation/19.0/legal/licenses.html, прочитано 2026-11-11). AGPL у прикладах не названо.
- **Висновки `[не перевірено юристом]`.** td_, що успадковує моделі AGPL-модуля або залежить від нього, найімовірніше, мусить поширюватися під AGPL-3, а не під OPL-1 чи іншою пропрієтарною ліцензією. Тоді «наша підписка на td_» — плата за супровід, а не за ліцензію, а партнери можуть легально копіювати td_. Чи сумісні AGPL-модулі з ліцензією EE (варіант «EE-клієнт отримує те саме ядро») — питання юриста. Варіанти для власника — FUNCTIONAL-MAP §7 п. 14, ризик R-19.

**Колізії моделей (F, код).** `helpdesk_mgmt` → `helpdesk.ticket`, як і EE Helpdesk (§7.5). `fieldservice` → `fsm.order`, `sign_oca` → `sign.oca.request` (https://github.com/OCA/sign/blob/19.0/sign_oca/models/sign_oca_request.py, прочитано 2026-11-11) — власні назви, колізій з EE за назвою не видно.

**Оновлення версій (F).** «Version Upgrades» — ✗ для CE (§7.1). OpenUpgrade: гілка `20.0` у https://github.com/OCA/OpenUpgrade є (`git ls-remote`, 2026-11-11). Які модулі покриває міграція 19→20 — `[не перевірено]`. Odoo 20.0 уже опублікована: у https://github.com/odoo/odoo/blob/20.0/odoo/release.py — `version_info = (20, 0, 0, FINAL, 0, '')` (прочитано 2026-11-11); дату релізу не перевіряли. OCA-модулі переходять на 20.0 у темпі спільноти; td_ переносимо самі (D-03).

**Мобільний інтерфейс (F / `[не перевірено]`).** «Mobile • Android and iOS» — ✗ для CE; «Desktop • Web Browser» — ✓ для обох (§7.1). Польові екрани CE (замір, планшет цеху, акт монтажу, нарахування) — веб-клієнт у браузері телефону чи планшета + OCA `web_responsive` (LGPL-3, Production/Stable, §7.3) + td_ мобільні подання. Придатність на телефоні й планшеті, фото з камери, підпис пальцем, робота при слабкому зв'язку на об'єкті — `[не перевірено на телефоні/планшеті]`.

**Облік часу на CE (F, код)** — §7.2: запис на користувача, не на працівника.
