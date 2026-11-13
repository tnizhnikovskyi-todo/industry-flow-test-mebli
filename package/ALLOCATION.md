# ALLOCATION — розподіл AC пакета mebli за треками й модулями (A-10)

Вхід: ТР `package/SPEC.md` (A-08, спроби 1–2: §4 AC, §5 трасування, §11 VP), технічний дизайн `package/tr/` (`00-architecture.md` §1–§4), схема `package/templates/answers.yaml` (A-09). Одна строка — один AC; трек, модуль і коробка — з рядка «Трасування» SPEC (трек ТР не перерозподіляється). Читають: A-11 (код `td_mebli_*`), A-12 `config-as-code` (рядки «стандарт» / «конфіг», колонка «модуль Odoo (технічна назва)», VP → параметр), A-13 `master-data-template-builder`, A-14 `gates-aggregator` / flow-autocheck (AC ↔ ALLOCATION). Скіла пакета для A-10 немає — формат за входами наступних кроків (`observations/2026-11-13-a10-no-skill.md`).

## Як читати
- **Трек** (контракт flow-autocheck `checks/A-10.yaml`): `стандарт` — стандартна поведінка Odoo 19 без налаштування пакета; `конфіг` — налаштування/дані конфіг-пакета A-12 без коду; `код` — наш модуль `td_mebli_*` (A-11); `готове` — готовий модуль ToDo (A-03c). Рядків «готове» — 0: REUSE-01 `td_sale_cost` — ідея без копіювання коду (SPEC AI-A08-08), REUSE-02…06 — «ні» (`research/REUSE.md`).
- **Вид** — уточнення ТР: `стандарт CE`, `конфіг`, `td_` (функція в `td_mebli_*`), `інтеграція` (обмін із зовнішньою системою — `td_mebli_bas`, `td_mebli_migration`), `EE-міст` (модуль-міст до додатка Enterprise, `auto_install`, лише профіль `ee`). Інтеграції й мости — трек `код`, бо це наші модулі.
- **Модуль Odoo (технічна назва)** — для «стандарт» / «конфіг»: лише технічні назви через кому (стандартні модулі й `td_*`, які мають бути встановлені); для «код» — модулі `td_mebli_*`, у яких реалізація.
- **Коробка** — A / B / C (SPEC §1.1); light — профіль із модулів A (`00-architecture.md` §3). **VP** — точки варіативності SPEC §11 (з рядка трасування), `edition` / `contract_mode` — службові параметри.
- **Крок** — хто реалізує: A-11 (код), A-12 (конфіг-пакет: модулі, налаштування, значення VP), A-13 (шаблони майстер-даних).

## Розподіл AC (SPEC §4)

| AC | Назва AC | F-xx | Трек | Вид | Модуль Odoo (технічна назва) | Коробка | VP | Крок | Примітка |
|---|---|---|---|---|---|---|---|---|---|
| AC-001 | Заявка в CRM і зустріч заміру в календарі | F-48 | стандарт | стандарт CE | crm, calendar | A | — | A-12 | — |
| AC-002 | Вільні вікна замірника | F-54 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-003 | Немає вільних вікон | F-54 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-004 | Нагадування покупцю про замір | F-51 | конфіг | конфіг | calendar | A | — | A-12 | конфіг-пакет |
| AC-005 | Замір-лист у картці замовлення | F-19 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-006 | Замірник бачить лише свої заміри і без цін | F-19 | код | td_ | td_mebli_measure, td_mebli_base | A | — | A-11 | — |
| AC-007 | Замір на телефоні | F-19 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-008 | Техніка не вміщається в нішу | F-20 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-009 | Звірка трьох чисел із модулем специфікації | F-20 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-010 | Порожні розміри — без хибної тривоги | F-20 | код | td_ | td_mebli_measure | A | — | A-11 | — |
| AC-011 | Несумісні опції не пропонуються | F-03 | конфіг | конфіг | product, td_mebli_mrp | B | VP-02 | A-12 (+ A-11: td_mebli_mrp) | конфіг-пакет |
| AC-012 | Розміри поза межами виробу | F-03 | код | td_ | td_mebli_mrp | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-013 | Чернетка специфікації з опцій | F-04 | код | td_ | td_mebli_mrp, td_mebli_sale | A | — | A-11 | — |
| AC-014 | Кілька виробів в одному замовленні | F-04 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-015 | Ціна з розмірів | F-24 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-016 | Виріб без формули | F-24 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-017 | Собівартість і маржа до запуску | F-21 | код | td_ | td_mebli_sale | A | VP-08 | A-11 (+ A-12: значення VP) | — |
| AC-018 | Видимість маржі менеджеру — параметр | F-21 | код | td_ | td_mebli_base | A | VP-08 | A-11 (+ A-12: значення VP) | — |
| AC-019 | Графік оплат етапами | F-22 | конфіг | конфіг | account, td_mebli_sale | A | VP-05 | A-12 (+ A-11: td_mebli_sale) | конфіг-пакет |
| AC-020 | Контроль доплати перед виїздом | F-22 | код | td_ | td_mebli_install | A | VP-05, VP-06 | A-11 (+ A-12: значення VP) | — |
| AC-021 | Ручна позначка оплати з причиною | F-22 | код | td_ | td_mebli_install | A | VP-04, VP-06 | A-11 (+ A-12: значення VP) | — |
| AC-022 | Прогнозна дата й банер зсуву | F-23 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-023 | Прогноз без МО і без обіцяної дати | F-23 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-024 | Замовна позиція зсуває прогноз | F-36 | конфіг | конфіг | stock, purchase_stock, td_mebli_sale | A | — | A-12 (+ A-11: td_mebli_sale) | конфіг-пакет |
| AC-025 | Надійність постачальника за історією | F-63 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-026 | Порізка в дистриб'ютора в прогнозній даті | F-28 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-027 | Дистриб'ютора порізки не задано | F-28 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-028 | Відправлена версія фіксується | F-28 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-029 | Сповіщення менеджеру про зсув | F-50 | код | td_ | td_mebli_notify | A | — | A-11 | — |
| AC-030 | Листи покупцю за шаблоном | F-51 | конфіг | конфіг | mail, td_mebli_notify | A | — | A-12 (+ A-11: td_mebli_notify) | конфіг-пакет, шаблони td_mebli_notify |
| AC-031 | Автоматичне нагадування про доплату | F-51 | код | td_ | td_mebli_notify | A | VP-05, VP-07 | A-11 (+ A-12: значення VP) | — |
| AC-032 | Візуалізація проєкту в КП | F-53 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-033 | Договір у режимі компанії | F-49 | код | td_ | td_mebli_sale | A | `contract_mode` | A-11 (+ A-12: значення VP) | — |
| AC-034 | Режим договору не задано | F-49 | код | td_ | td_mebli_sale, td_mebli_base | A | `contract_mode` | A-11 (+ A-12: значення VP) | — |
| AC-035 | Юрособа-продавець і монтаж від ФОП | F-25 | код | td_ | td_mebli_multico | B | VP-03 | A-11 (+ A-12: значення VP) | — |
| AC-036 | Доступ за юрособами | F-25 | код | td_ | td_mebli_base | A | VP-03 | A-11 (+ A-12: значення VP) | правила на всіх td_-моделях |
| AC-037 | Курс НБУ і перерахунок цін | F-26 | код | td_ | td_mebli_ua | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-038 | НБУ недоступний | F-26 | код | td_ | td_mebli_ua | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-039 | Обмін документами з BAS | F-47 | код | інтеграція | td_mebli_bas | A | VP-04 | A-11 (+ A-12: значення VP) | — |
| AC-040 | Помилка обміну | F-47 | код | інтеграція | td_mebli_bas | A | VP-04 | A-11 (+ A-12: значення VP) | — |
| AC-041 | Документ у BAS не змінюється в Odoo | F-47 | код | інтеграція | td_mebli_bas | A | VP-04 | A-11 (+ A-12: значення VP) | — |
| AC-042 | Оплати з BAS закривають етапи | F-47 | код | інтеграція | td_mebli_bas, td_mebli_install | A | VP-04, VP-05 | A-11 (+ A-12: значення VP) | — |
| AC-043 | Задача монтажу із замовлення | F-15 | конфіг | конфіг | sale_project | A | VP-16 | A-12 | конфіг-пакет |
| AC-044 | Задачі монтажу немає до підтвердження | F-15 | стандарт | стандарт CE | sale_project | A | — | A-12 | — |
| AC-045 | Імпорт специфікації CSV / Excel | F-01 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-046 | Немає обов'язкових колонок | F-01 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-047 | Невідомий матеріал | F-01 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-048 | Імпорт 300 деталей | F-01 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-049 | Шаблон мапінгу колонок | F-27 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-050 | AI-підказка мапінгу | F-27 | код | td_ | td_mebli_mrp | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-051 | Одна специфікація для продажу, розкрою й обліку | F-02 | код | td_ | td_mebli_mrp, td_mebli_sale | A | — | A-11 | — |
| AC-052 | Специфікація після відправлення в розкрій | F-02 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-053 | Передача деталей на свій розкрій | F-05 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-054 | МО без деталей | F-05 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-055 | Перевірка проєкту за заміром перед розкроєм | F-62 | код | td_ | td_mebli_cutting, td_mebli_measure | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-056 | Заміру немає | F-62 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-057 | Пакет розкрою кількох замовлень одного декору | F-30 | код | td_ | td_mebli_cutting | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-058 | Різні декори в пакеті | F-30 | код | td_ | td_mebli_cutting | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-059 | Ділові обрізки після розкрою | F-11 | код | td_ | td_mebli_cutting | B | VP-02, VP-12 | A-11 (+ A-12: значення VP) | — |
| AC-060 | Підбір обрізка під деталь | F-11 | код | td_ | td_mebli_cutting | B | VP-02, VP-12 | A-11 (+ A-12: значення VP) | — |
| AC-061 | Етикетки деталей з QR | F-29 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-062 | Сканування етикетки при комплектації | F-29 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-063 | Етап рахується з документів | F-07 | код | td_ | td_mebli_sale, td_mebli_install | A | — | A-11 | — |
| AC-064 | Ручне перетягування етапу заборонено | F-07 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-065 | Акт без повної оплати | F-07 | код | td_ | td_mebli_install | A | VP-05 | A-11 (+ A-12: значення VP) | — |
| AC-066 | Причина зсуву на картці | F-31 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-067 | Застряглі замовлення | F-07 | код | td_ | td_mebli_sale, td_mebli_base | A | VP-10 | A-11 (+ A-12: значення VP) | — |
| AC-068 | МО зі специфікацією й маршрутом замовлення | F-06 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-069 | Завантаження дільниць без Ганта | F-33 | код | td_ | td_mebli_mrp | A | — | A-11 | — |
| AC-070 | Простій і перенесення завдань | F-08 | конфіг | конфіг | mrp | A | — | A-12 | конфіг-пакет: причини втрат |
| AC-071 | Кіоск завдань за PIN | F-32 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-072 | Другий працівник на тому самому завданні | F-32 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-073 | Брак у цеху → повторна деталь | F-18 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-074 | Крок якості з фото | F-34 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-075 | «Зроблено» без перевірки | F-34 | код | td_ | td_mebli_shop | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-076 | Обслуговування верстатів дільниць | F-60 | код | td_ | td_mebli_maint | A | — | A-11 | — |
| AC-077 | Прихід на зміну в кіоску відвідувань | F-61 | стандарт | стандарт CE | hr_attendance | A | — | A-12 | — |
| AC-078 | Табель для BAS | F-61 | код | інтеграція | td_mebli_attendance, td_mebli_bas | A | VP-04 | A-11 (+ A-12: значення VP) | — |
| AC-079 | Табло цеху на ТВ | F-65 | код | td_ | td_mebli_dashboard | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-080 | Повторне виготовлення з рекламації | F-18 | код | td_ | td_mebli_claim | A | — | A-11 | — |
| AC-081 | Рекламація без деталі | F-18 | код | td_ | td_mebli_claim | A | — | A-11 | — |
| AC-082 | Резерв і нестача під замовлення | F-10 | стандарт | стандарт CE | stock, mrp | A | — | A-12 | — |
| AC-083 | Затримані поставки й зачеплені замовлення | F-09 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-084 | Ціни закупівлі в динаміці | F-12 | стандарт | стандарт CE | purchase | A | — | A-12 | — |
| AC-085 | Ціна вища за історію | F-35 | код | td_ | td_mebli_purchase | A | VP-11 | A-11 (+ A-12: значення VP) | — |
| AC-086 | Немає історії цін | F-35 | код | td_ | td_mebli_purchase | A | VP-11 | A-11 (+ A-12: значення VP) | — |
| AC-087 | Імпорт прайсу постачальника з Excel | F-59 | код | td_ | td_mebli_purchase | A | — | A-11 | — |
| AC-088 | Аналог матеріалу | F-57 | код | td_ | td_mebli_mrp | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-089 | Повна міграція з BAS/BAF і БАЗИС | F-46 | код | інтеграція | td_mebli_migration | B | VP-01 | A-11 + A-13 (шаблони імпорту) (+ A-12: значення VP) | — |
| AC-090 | Розбіжність звірки міграції | F-46 | код | інтеграція | td_mebli_migration | A | — | A-11 + A-13 (шаблони імпорту) | шаблони A-13 |
| AC-091 | Комплектувальний лист по місцях | F-37 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-092 | Неповний комплект не відвантажується | F-37 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-093 | Дозамовлення відсутньої деталі | F-37 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-094 | Друк комплектувального листа | F-49 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-095 | Графік бригад | F-38 | конфіг | конфіг | project | A | — | A-12 | конфіг-пакет |
| AC-096 | Денний план бригади | F-58 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-097 | Акт монтажу з підписом | F-39 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-098 | Підпис без підпису / зміна підписаного | F-39 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-099 | Бригада бачить лише свої виїзди | F-39 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-100 | Фото у фотоархів лише зі згодою | F-40 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-101 | Акт приймання-передачі без монтажу | F-56 | код | td_ | td_mebli_install | A | `contract_mode` | A-11 (+ A-12: значення VP) | — |
| AC-102 | Друк акта монтажу | F-49 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-103 | Монтаж у кілька виїздів | F-38 | код | td_ | td_mebli_install | A | VP-15 | A-11 (+ A-12: значення VP) | — |
| AC-104 | Відрядна й відсоток бригаді | F-41 | код | td_ | td_mebli_install | A | VP-14, VP-15 | A-11 (+ A-12: значення VP) | — |
| AC-105 | Операція без розцінки | F-41 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-106 | Працівник бачить лише своє; підтверджене не змінюється | F-41 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-107 | Премія або штраф з причиною | F-42 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-108 | Премія без причини | F-42 | код | td_ | td_mebli_install | A | — | A-11 | — |
| AC-109 | Передача нарахувань у BAS | F-41 | код | інтеграція | td_mebli_bas | A | VP-04 | A-11 (+ A-12: значення VP) | — |
| AC-110 | Реєстрація рекламації | F-17 | код | td_ | td_mebli_claim | A | VP-13 | A-11 (+ A-12: значення VP) | — |
| AC-111 | Гарантія за строком категорії | F-17 | код | td_ | td_mebli_claim | A | — | A-11 | — |
| AC-112 | Платний ремонт після гарантії | F-55 | код | td_ | td_mebli_claim | A | — | A-11 | — |
| AC-113 | Міст Helpdesk | F-17 | код | EE-міст | td_mebli_helpdesk | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-114 | План і факт собівартості замовлення | F-14 | код | td_ | td_mebli_cost | A | — | A-11 | — |
| AC-115 | Собівартість лише для дозволених груп | F-14 | код | td_ | td_mebli_cost, td_mebli_base | A | — | A-11 | — |
| AC-116 | Перевитрата матеріалу | F-52 | конфіг | конфіг | mrp, td_mebli_mrp | A | VP-17 | A-12 (+ A-11: td_mebli_mrp) | конфіг-пакет |
| AC-117 | Підпис пропозиції порталом | F-43 | конфіг | конфіг | sale, portal | A | — | A-12 | конфіг-пакет |
| AC-118 | Зміна замовлення: версія, ціна, дата, причина | F-44 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-119 | Зміна після відправлення в розкрій | F-44 | код | td_ | td_mebli_sale | A | — | A-11 | — |
| AC-120 | Зміна на підпис клієнту | F-44 | код | td_ | td_mebli_sale | B | VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-121 | Показники з переходом до записів | F-45 | код | td_ | td_mebli_dashboard | A | VP-01, VP-02 | A-11 (+ A-12: значення VP) | — |
| AC-122 | Дашборд лише для керівника | F-45 | код | td_ | td_mebli_dashboard, td_mebli_base | A | — | A-11 | — |
| AC-123 | Порожні дані | F-45 | код | td_ | td_mebli_dashboard | A | — | A-11 | — |
| AC-124 | Ранковий брифінг | F-64 | код | td_ | td_mebli_notify | A | VP-10, VP-13 | A-11 (+ A-12: значення VP) | — |
| AC-125 | Нічого звітувати | F-64 | код | td_ | td_mebli_notify | A | — | A-11 | — |
| AC-126 | Міст Shop Floor | F-32 | код | EE-міст | td_mebli_shopfloor | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-127 | Міст Quality | F-34 | код | EE-міст | td_mebli_quality | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-128 | Міст Field Service і Planning | F-38 | код | EE-міст | td_mebli_fsm, td_mebli_planning | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-129 | Міст Sign | F-43 | код | EE-міст | td_mebli_sign | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-130 | Без EE мости не ставляться | F-39 | код | EE-міст | td_mebli_shopfloor, td_mebli_quality, td_mebli_fsm, td_mebli_planning, td_mebli_helpdesk, td_mebli_sign | C | `edition` | A-11 (+ A-12: значення VP) | auto_install; лише профіль ee; перевірка після ВП-4 |
| AC-131 | Імпорт результату розкрою | F-05 | код | td_ | td_mebli_cutting | A | VP-09 | A-11 (+ A-12: значення VP) | — |
| AC-132 | Виїзд за рекламацією | F-17 | код | td_ | td_mebli_claim | A | — | A-11 | — |
| AC-133 | Паперовий наряд при відключенні світла | F-08 | код | td_ | td_mebli_shop | A | — | A-11 | — |
| AC-134 | Відомість нарахувань | F-41 | код | td_ | td_mebli_install | A | — | A-11 | — |

### Підсумок (за SPEC §5)

| Трек | AC |
|---|---|
| стандарт | 5 |
| конфіг | 10 |
| код | 119 |
| готове | 0 |

| Вид | AC |
|---|---|
| стандарт CE | 5 |
| конфіг | 10 |
| td_ | 105 |
| інтеграція | 8 |
| EE-міст | 6 |

| Коробка | AC |
|---|---|
| A | 108 |
| B | 20 |
| C | 6 |

| Крок-виконавець | AC |
|---|---|
| A-11 | 119 |
| A-12 | 15 |
| A-12 з модулем A-11 | 5 |
| A-11 + значення VP A-12 | 57 |
| A-13 | 2 |

## Нефункціональні (SPEC §4.17, AC-N.xx)

| NFR | Назва | Трек | Модуль / де | Коробка | VP | Крок |
|---|---|---|---|---|---|---|
| AC-N.01 | Мова | конфіг | base (мова uk_UA), `i18n/uk.po` усіх `td_mebli_*` | усі | — | A-12 (мова), A-11 (переклади) |
| AC-N.02 | Продуктивність | код | td_mebli_sale, td_mebli_mrp, td_mebli_shop | A | — | A-11; вимір — A-15/A-16 |
| AC-N.03 | ПДВ і план рахунків | конфіг | l10n_ua, account | усі | VP-18 | A-12 (AI-A08-11) |
| AC-N.04 | Оновлення без втрати даних | код | `migrations/19.0.1.1.0/` модулів зрізу | усі | — | A-11 (AI-A08-19) |
| AC-N.05 | Резервні копії CE | інфраструктура (поза Odoo) | сервер і сховище, не модуль | усі | — | C-00 / хостинг (не A-11…A-13) |
| AC-N.06 | Кирилиця в PDF | код | td_mebli_base (шрифт, AI-A08-20) | усі | — | A-11 |
| AC-N.07 | Профіль коробки | конфіг | td_mebli_base (feature-групи), профіль конфіг-пакета | A, B | VP-01, VP-02 | A-12 (+ A-11 групи) |

## Точки варіативності → трек і параметр (SPEC §11; для `vp-map.yaml` A-12)

| VP / ключ | Параметр | Трек | Вид параметра (`kind`) | Де в Odoo | Модуль | Залежні AC | Крок |
|---|---|---|---|---|---|---|---|
| VP-01 | Профіль коробки | конфіг | профіль модулів + group | manifest `edition_profiles` + feature-групи; `res.company.td_box_profile` | td_mebli_base | AC-N.07, AC-089, AC-121 | A-12 |
| VP-02 | Функції коробки B | конфіг | group | `res.config.settings` → `td_mebli_base.group_feature_<значення>` (`implied_group`) | td_mebli_base | AC-011, AC-012, AC-037, AC-038, AC-050, AC-057, AC-058, AC-059, AC-060, AC-062, AC-071, AC-072, AC-073, AC-074, AC-075, AC-079, AC-088, AC-120, AC-121 | A-12 (групи створює A-11) |
| VP-03 | Юрособи компанії | конфіг | record + модуль | `res.company` (юрособи — B-04); `multi_install_fop` → модуль `td_mebli_multico` | base, td_mebli_multico | AC-035, AC-036 | A-12 (+ A-11 модуль) |
| VP-04 | Обмін з BAS/BAF | конфіг | модуль | установка `td_mebli_bas` лише при `true` | td_mebli_bas | AC-021, AC-039, AC-040, AC-041, AC-042, AC-078, AC-109 | A-12 (+ A-11 модуль) |
| VP-05 | Оплата замовлення етапами | конфіг | record | `account.payment.term` з етапами; відсотки — B-04 | account, td_mebli_sale | AC-019, AC-020, AC-031, AC-042, AC-065 | A-12 |
| VP-06 | Контроль доплати перед виїздом | код | td_param | `res.company.td_payment_control` | td_mebli_base | AC-020, AC-021 | A-11 поле, A-12 значення |
| VP-07 | Нагадування про доплату, днів до виїзду | код | td_param | `res.company.td_pay_reminder_days` | td_mebli_base | AC-031 | A-11 поле, A-12 значення |
| VP-08 | Менеджер бачить маржу | код | td_param | `res.company.td_margin_to_salesman` | td_mebli_base | AC-017, AC-018 | A-11 поле, A-12 значення |
| VP-09 | Розкрій плит | код | td_param | меню власного розкрою ховається для `distributor` (механізм — A-11) | td_mebli_cutting | AC-026, AC-027, AC-028, AC-053, AC-054, AC-055, AC-056, AC-131 | A-11 механізм, A-12 значення |
| VP-10 | Застряглі замовлення, днів без руху | код | td_param | `res.company.td_stuck_days` | td_mebli_base | AC-067, AC-124 | A-11 поле, A-12 значення |
| VP-11 | Поріг ціни закупівлі вище історії, % | код | td_param | `res.company.td_price_threshold_pct` | td_mebli_base | AC-085, AC-086 | A-11 поле, A-12 значення |
| VP-12 | Мінімальний діловий обрізок, мм | код | td_param | `res.company.td_min_offcut_mm` | td_mebli_base | AC-059, AC-060 | A-11 поле, A-12 значення |
| VP-13 | Строк закриття рекламації, днів | код | td_param | `res.company.td_claim_overdue_days` | td_mebli_base | AC-110, AC-124 | A-11 поле, A-12 значення |
| VP-14 | Поділ % бригаді між виконавцями | код | td_param | `res.company.td_crew_split` | td_mebli_base | AC-104 | A-11 поле, A-12 значення |
| VP-15 | База нарахування % бригаді | код | td_param | `res.company.td_crew_base` | td_mebli_base | AC-103, AC-104 | A-11 поле, A-12 значення |
| VP-16 | Монтаж у вартості замовлення | код | td_param | `res.company.td_install_in_price` | td_mebli_base | AC-043 | A-11 поле, A-12 значення |
| VP-17 | Перевитрата матеріалу у виробництві | конфіг | record | `mrp.bom.consumption` специфікацій (перенесення на специфікації замовлення — A-11, AI-A08-27) | mrp, td_mebli_mrp | AC-116 | A-12 (+ A-11) |
| VP-18 | Платник ПДВ | конфіг | record + модуль | `l10n_ua`, податки за замовчуванням компанії | l10n_ua, account | AC-N.03 | A-12 |
| edition | Редакція Odoo | конфіг | профіль модулів | manifest `edition_profiles: ce / ee` | мости EE | AC-113, AC-126…AC-130 | A-12 |
| contract_mode | Режим договору | код | td_param | `res.company.td_contract_mode` (`unset` → порожньо) | td_mebli_base | AC-033, AC-034, AC-101 | A-11 поле, A-12 значення |

Трек `код` для VP — поле `td_*` на `res.company` створює A-11 (`td_mebli_base`, `tr/td_mebli_base.md` §1); значення з `answers.yaml` ставить A-12 (`kind: td_param`, якір — поле компанії, AI-A08-04).

## Модулі до установки за профілями (SPEC §1.1, `tr/00-architecture.md` §1–§3)

| Профіль | Стандартні модулі Odoo (залежності, `origin: std-ce`) | Модулі `td_mebli_*` (`origin: td`), порядок установки |
|---|---|---|
| A (VP-01 `A`) | base_setup, mail, hr, crm, calendar, sale_crm, sale_margin, sale_mrp, sale_stock, sale_project, sale_purchase_stock, purchase_mrp, purchase_stock, purchase, mrp, mrp_account, stock, project, repair, portal, account, l10n_ua (VP-18), hr_attendance, hr_hourly_cost, maintenance, base_import | td_mebli_base, td_mebli_mrp, td_mebli_sale, td_mebli_measure, td_mebli_cutting, td_mebli_shop, td_mebli_install, td_mebli_claim, td_mebli_purchase, td_mebli_ua, td_mebli_maint, td_mebli_attendance, td_mebli_bas (VP-04 = `true`), td_mebli_cost, td_mebli_migration (шаблони), td_mebli_dashboard, td_mebli_notify |
| light (VP-01 `light`) | як A | як A без td_mebli_bas (VP-04 = `false`); за `depends` (`td_mebli_install` → `td_mebli_shop`, `td_mebli_dashboard` → «усі функціональні модулі A») решта модулів A теж ставиться — цех, нарахування, закупівлі ховає профіль (AI-A10-05) |
| B (VP-01 `B`) | як A | A + td_mebli_multico (VP-03 `multi_install_fop`); функції B — feature-групи VP-02 |
| C (VP-01 `B` + `edition: ee`) | B + EE: mrp_workorder, quality_control, industry_fsm, planning, helpdesk, sign (`origin: std-ee`) | B + мости `auto_install`: td_mebli_shopfloor, td_mebli_quality, td_mebli_fsm, td_mebli_planning, td_mebli_helpdesk, td_mebli_sign |

`td_mebli_demo` клієнтам не ставиться (лише демо A-15). Порядок `td_*` — за графом `00-architecture.md` §2.

## Формат конфіг-пакета й команда установки

Рішення AI (Архітектор рішення — вето): формат за замовчуванням `config-as-code/references/config-package-format.md` — `format: 2`, `editions: both` (OWNER-INTAKE), `edition_profiles: ce / ee` (ee ⊇ ce + мости), профілі коробок light / A / B — підмножини модулів `ce` за VP-01 (таблиця вище); `vp-map.yaml` — за таблицею «Точки варіативності» (SPEC §11). Установка в чисту тестову базу — скрипти `tools/odoo/` з еталонів `flow-core/references/templates/tools-odoo/` (C-00); доки C-00 не скопіював еталони — версія 1: вручну за runbook A-12 з `install-log.md`. Базу клієнта не чіпає (B-04).

## Рішення AI з ризиком (власник — вето; записи 28, 37, 48)

| ID | Рішення | Альтернатива | Ризик | Перевірка |
|---|---|---|---|---|
| AI-A10-01 | Інтеграції (`td_mebli_bas`, `td_mebli_migration`) і мости EE — трек `код` (наші модулі), вид — окремою колонкою | окремі треки «інтеграція» / «EE-міст» | флоу-автоперевірка знає лише 4 треки; A-12 мусить читати «Вид», щоб не ставити мости в `ce` | A-14 track-convergence |
| AI-A10-02 | Трек кожного AC — дослівно з SPEC, без перерозподілу; конфіг-рядки з `td_*` модулем — крок A-12 з передумовою модуля A-11 | перенести такі AC у «код» | A-12 стартує до готовності модуля | A-12 Крок 1 (передумови) |
| AI-A10-03 | AC-N.xx — окремою таблицею (не потрапляють у шаблон `AC-\d{2,3}`); AC-N.05 — інфраструктура поза кроками A-11…A-13 | рядки в основній таблиці з треком «стандарт» | бекап ніхто не реалізує в A-11…A-13 | C-00 / хостинг; A-17 |
| AI-A10-04 | VP з полем `td_*` на компанії — трек `код` (поле A-11), значення — A-12 `kind: td_param` | трек `конфіг` | A-12 без поля A-11 не застосує значення | A-12 read-back |
| AI-A10-05 | Профіль light = модулі A без `td_mebli_bas`; цех, нарахування, закупівлі ховаються профілем, бо за `depends` SPEC (`td_mebli_install` → `td_mebli_shop`, `td_mebli_dashboard` → усі функціональні A) окремий набір модулів неможливий (SPEC `00-architecture.md` §3 каже «без `_shop`, `_attendance`, `_maint`») | розірвати залежності в A-11 | ширша поверхня оновлень у мікроцехів; розбіжність зі SPEC | A-11 (беклог), відкрите питання |

## Відкриті питання
- Профіль light (AI-A10-05): A-11 / Архітектор вирішують, чи розривати залежності `td_mebli_install` → `td_mebli_shop` і `td_mebli_dashboard` → усі модулі A (SPEC `00-architecture.md` §3 «без `_shop`, `_bas`, `_attendance`, `_maint`»).
- Модулі EE (мости, `mrp_workorder`, `quality_control`, `industry_fsm`, `planning`, `helpdesk`, `sign`) не перевірено на Odoo 19 EE — доступу немає (SPEC ВП-4); `module-exists` — MANUAL.
- `td_mebli_notify`, `td_mebli_maint`, `td_mebli_attendance` — хвиля 2 зрізу, у базі кроку їх немає (SPEC R-01).

## Затвердження (заповнює людина)
Предмет затвердження: розподіл AC SPEC §4 і VP SPEC §11 за треками, модулями й кроками (цей файл).

Архітектор рішення: — ; дата: — ; рішення: —
