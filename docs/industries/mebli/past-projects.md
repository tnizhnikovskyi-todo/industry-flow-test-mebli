# Минулі проєкти в галузі: меблі (КВЕД-2010, розділ 31)

Статус: чернетка AI (A-04), 2026-11-10. Вхід: `decision.md@aa27e3e`. Лише коди П-xx й ідентифікатори джерел; відповідність код -> проєкт
лише в `_input/sources.md` (робоча тека, поза git).

Формули ідентифікаторів: `aikb:<doc_id>`, `fathom:<recording_id>`, `repo:<шлях>@<sha>`. Тут `repo:todo_timur/…` — репозиторій
з колонки «репозиторії» `sources.md`; `@0976f05` — інтеграційна гілка збірки модулів, `@adce004` — гілка за замовчуванням (README, процеси).

## Проєкти й джерела

| П-xx | У галузі | У сегменті + підстава | Режим читання | Типи джерел | Ідентифікатори |
|---|---|---|---|---|---|
| П-01 | так | невідомо: внутрішній демо-проєкт без клієнта; у демо-компанії на зміну 1 відмічено 35 співробітників, загальна чисельність не вказана (repo:todo_timur/factory3d/README.md@adce004) | повний (AIKB-проєкту немає; Fathom вимкнено DATA_POLICY) | код, README, журнал збірки | repo:todo_timur/factory3d/README.md@adce004, repo:todo_timur/factory3d/build/BUILD_STATUS.md@adce004, repo:todo_timur/factory3d/odoo_addons@0976f05 |

## Що вже робили

| Процес | Що зроблено | Кількість П-xx | Джерела |
|---|---|---|---|
| Склад матеріалів і фурнітури | комірки зі штрихкодом, партії плит, крайки й ЛФМ, одиниці «аркуш, м, шт, комплект, кг, рулон», упаковки готової продукції на палетах | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004 |
| Маршрути складу | приймання у 2 кроки, плити — у 3 через вхідний контроль, відвантаження у 2 кроки, поповнення під розкрійний портал зі стелажів | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004; repo:todo_timur/factory3d/plant/odoo_flows.py@adce004 |
| Поповнення і закупівля | правила мін/макс для комірок фурнітури й стосів плит, закупівлі з правил поповнення | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004 |
| Виробництво за маршрутами | робочі центри за дільницями (розкрій, крайкооблицювання, присадка тощо), специфікації «виріб + лінія» з операціями, МО і робочі завдання, списання компонентів на операції | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004 |
| Фасади як окреме виробництво | дочірні МО фасадів до МО корпусів; фасад — компонент МО корпусу, що чекає на дочірнє МО | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004 |
| Стани верстатів, простої, OEE | журнал станів і простоїв з причинами, автостарт/пауза/завершення робочих завдань, OEE з фактичних даних, аналіз вузького місця | 1 (П-01) | П-01 repo:todo_timur/factory3d/odoo_addons/td_machine_connect@0976f05 |
| Склад плит розкрійного порталу | стоси порталу проти складських залишків, завдання порталу з МО; карти розкрою й програми ЧПУ прикріплюються до МО | 1 (П-01) | П-01 repo:todo_timur/factory3d/odoo_addons/td_machine_connect@0976f05 |
| Собівартість і маржа замовлення | фактична собівартість і маржа замовлення продажу за верстатами, енергією, матеріалами й відходами, план проти факту | 1 (П-01) | П-01 repo:todo_timur/factory3d/odoo_addons/td_sale_cost@0976f05 |
| Енергоспоживання на виробництві | лічильники, 15-хвилинний профіль, кВт·год і вартість на робоче завдання, тарифи, ліміт потужності | 1 (П-01) | П-01 repo:todo_timur/factory3d/odoo_addons/td_energy@0976f05 |
| Контроль якості | точки «вхідний контроль плит» і «контроль збирання», брак із претензією постачальнику | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004 |
| Обслуговування обладнання | паспорти обладнання, планове ТО, заявки; сигнали обладнання з порогами, що створюють заявку на ТО | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004; repo:todo_timur/factory3d/odoo_addons/td_telemetry@0976f05 |
| Логістика воріт і двору | поля «ворота, фура, техніка» на переміщеннях, пакетні переміщення біля воріт, бронювання воріт, рейси фур, ваги | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004; repo:todo_timur/factory3d/odoo_addons/td_yard@0976f05 |
| Облік робочого часу | зміна і графік, відмітки відвідування через СКУД, картки й турнікети | 1 (П-01) | П-01 repo:todo_timur/factory3d/README.md@adce004; repo:todo_timur/factory3d/odoo_addons/td_access@0976f05 |
| Візуалізація заводу | 3D-переглядач у Odoo з живими даними ORM, кнопка «Показати в 3D», кіоск цеху | 1 (П-01) | П-01 repo:todo_timur/factory3d/odoo_addons/td_viewer3d@0976f05 |

### Повторювані вимоги

Лише вимоги, що трапляються у >=2 різних П-xx.

| Вимога | П-xx (>=2) | Джерела |
|---|---|---|
| немає даних: проаналізовано один проєкт (П-01), повторюваність не визначається | - | - |

## Модулі для повторного використання

| Модуль (техн. назва) | Шлях | Версія Odoo | Сумісність з 19 | Що закриває | П-xx | Джерело |
|---|---|---|---|---|---|---|
| td_factory3d | todo_timur/factory3d/odoo_addons/td_factory3d | 19.0.1.0.2 | так | база комплексу: коди об'єктів, зони цеху, ворота, паспорти обладнання, групи доступу | П-01 | repo:todo_timur/factory3d/odoo_addons/td_factory3d@0976f05 |
| td_machine_connect | todo_timur/factory3d/odoo_addons/td_machine_connect | 19.0.1.4.5 | так | стани деревообробних верстатів, простої, автостарт робочих завдань, OEE, склад плит порталу, карти розкрою при МО | П-01 | repo:todo_timur/factory3d/odoo_addons/td_machine_connect@0976f05 |
| td_sale_cost | todo_timur/factory3d/odoo_addons/td_sale_cost | 19.0.1.1.1 | так | фактична собівартість і маржа замовлення продажу з даних виробництва | П-01 | repo:todo_timur/factory3d/odoo_addons/td_sale_cost@0976f05 |
| td_energy | todo_timur/factory3d/odoo_addons/td_energy | 19.0.1.1.6 | так | енергоспоживання, кВт·год і вартість на робоче завдання, тарифи | П-01 | repo:todo_timur/factory3d/odoo_addons/td_energy@0976f05 |
| td_energy_resources | todo_timur/factory3d/odoo_addons/td_energy_resources | 19.0.1.0.2 | так | облік газу, тепла, стисненого повітря й води, вартість | П-01 | repo:todo_timur/factory3d/odoo_addons/td_energy_resources@0976f05 |
| td_energy_analytics | todo_timur/factory3d/odoo_addons/td_energy_analytics | 19.0.1.1.0 | так | енергоаналітика: базова лінія ISO 50001, EnPI, бюджет, звіти | П-01 | repo:todo_timur/factory3d/odoo_addons/td_energy_analytics@0976f05 |
| td_energy_control | todo_timur/factory3d/odoo_addons/td_energy_control | 19.0.1.0.3 | так | сценарії автоматизації, пріоритети відключення навантаження, команди з блокуваннями | П-01 | repo:todo_timur/factory3d/odoo_addons/td_energy_control@0976f05 |
| td_energy_mobile | todo_timur/factory3d/odoo_addons/td_energy_mobile | 19.0.1.0.0 | так | мобільний екран чергового енергетика: обходи, чек-листи | П-01 | repo:todo_timur/factory3d/odoo_addons/td_energy_mobile@0976f05 |
| td_telemetry | todo_timur/factory3d/odoo_addons/td_telemetry | 19.0.1.1.6 | так | збір даних з обладнання: джерела, сигнали, показання, пороги -> заявки на ТО | П-01 | repo:todo_timur/factory3d/odoo_addons/td_telemetry@0976f05 |
| td_iot_sim | todo_timur/factory3d/odoo_addons/td_iot_sim | 19.0.2.3.0 | так | симулятор обладнання для демо: реєстр пристроїв, каталог сигналів, сценарії | П-01 | repo:todo_timur/factory3d/odoo_addons/td_iot_sim@0976f05 |
| factory3d_iot_sim | todo_timur/factory3d/odoo_addons/factory3d_iot_sim | 19.0.1.0.0 | так | data-модуль без Python: імітація сигналів обладнання і заявки на ТО за порогом (гілка за замовчуванням) | П-01 | repo:todo_timur/factory3d/odoo_addons/factory3d_iot_sim@adce004 |
| td_live_production | todo_timur/factory3d/odoo_addons/td_live_production | 19.0.1.0.9 | так | лише демо-стенд: щоденні замовлення, диспетчер робочих завдань, простої й відвантаження в реальному часі | П-01 | repo:todo_timur/factory3d/odoo_addons/td_live_production@0976f05 |
| td_yard | todo_timur/factory3d/odoo_addons/td_yard | 19.0.1.0.2 | так | двір: рейси фур, бронювання воріт, розпізнавання номерів, шлагбауми, ваги | П-01 | repo:todo_timur/factory3d/odoo_addons/td_yard@0976f05 |
| td_access | todo_timur/factory3d/odoo_addons/td_access | 19.0.1.1.0 | так | СКУД: відмітки відвідування, картки, турнікети, відвідувачі, люди за зонами | П-01 | repo:todo_timur/factory3d/odoo_addons/td_access@0976f05 |
| td_viewer3d | todo_timur/factory3d/odoo_addons/td_viewer3d | 19.0.1.1.15 | так | 3D-переглядач заводу в Odoo: живі дані, «Показати в 3D», кіоск цеху | П-01 | repo:todo_timur/factory3d/odoo_addons/td_viewer3d@0976f05 |
| td_constructor | todo_timur/factory3d/odoo_addons/td_constructor | 19.0.1.4.3 | так | конструктор планування заводу: майданчики, шари, шаблони стелажів, варіанти обладнання в 3D | П-01 | repo:todo_timur/factory3d/odoo_addons/td_constructor@0976f05 |
| td_bms | todo_timur/factory3d/odoo_addons/td_bms | 19.0.1.0.5 | так | освітлення за нормами, вентиляція й котельня, тепловий баланс | П-01 | repo:todo_timur/factory3d/odoo_addons/td_bms@0976f05 |
| td_fire_safety | todo_timur/factory3d/odoo_addons/td_fire_safety | 19.0.1.1.4 | так | пожежна сигналізація (читання), іскрогасіння, димовидалення, евакуація | П-01 | repo:todo_timur/factory3d/odoo_addons/td_fire_safety@0976f05 |
| td_genset | todo_timur/factory3d/odoo_addons/td_genset | 19.0.1.0.1 | так | моніторинг і керування генераторами через реле | П-01 | repo:todo_timur/factory3d/odoo_addons/td_genset@0976f05 |
| td_chp | todo_timur/factory3d/odoo_addons/td_chp | 19.0.1.0.0 | так | консоль оператора когенераційної установки | П-01 | repo:todo_timur/factory3d/odoo_addons/td_chp@0976f05 |
| td_claude_agent | todo_timur/factory3d/odoo_addons/td_claude_agent | 19.0.2.1.1 | так | AI-агент для користувача Odoo (не галузевий) | П-01 | repo:todo_timur/factory3d/odoo_addons/td_claude_agent@0976f05 |

Мости `auto_install` (ставляться разом з основними модулями, окремо не перелічено): `td_access_telemetry`, `td_chp_factory3d`,
`td_constructor_viewer3d`, `td_energy_resources_bms`, `td_energy_viewer3d`, `td_factory3d_mrp_maintenance`, `td_fire_safety_access`,
`td_fire_safety_viewer3d`, `td_genset_factory3d`, `td_machine_connect_mrp_workorder`, `td_machine_connect_viewer3d`,
`td_telemetry_viewer3d`, `td_viewer3d_sale`, `td_yard_gantt` (repo:todo_timur/factory3d/odoo_addons@0976f05). Модулі `test_td_*` — лише для тестів.

## Болі клієнтів

| Біль (переказ) | Частота (П-xx) | Джерела |
|---|---|---|
| немає даних: П-01 — внутрішній демо-проєкт без клієнта, болів клієнтів у джерелах немає; AIKB-проєкту немає, Fathom вимкнено | - | - |

## Прогалини

| Прогалина | Тип | П-xx | Джерела |
|---|---|---|---|
| Оптимізація розкрою плити й імпорт специфікацій із програм проєктування — у модулях немає: карти розкрою й програми ЧПУ лише прикріплюються до МО | не покрито модулями | П-01 | repo:todo_timur/factory3d/odoo_addons/td_machine_connect@0976f05 |
| Конфігуратор виробу на замовлення (опції, розміри, ціна) — серед маніфестів збірки немає | не покрито модулями | П-01 | repo:todo_timur/factory3d/odoo_addons@0976f05 |
| Користувачів для техніків і операторів свідомо не створювали: кожен — ліцензія Enterprise | свідомо не зроблено | П-01 | repo:todo_timur/factory3d/README.md@adce004 |
| Частковий випуск МО свідомо не робили: Odoo розбиває замовлення на дозамовлення з новими номерами | свідомо не зроблено | П-01 | repo:todo_timur/factory3d/README.md@adce004 |
| У демо-даних XML-RPC немає цін і собівартості, адрес партнерів, номерів фур — собівартість відпрацьована лише модулем td_sale_cost на демо-стенді | обмеженість аналізу | П-01 | repo:todo_timur/factory3d/README.md@adce004; repo:todo_timur/factory3d/odoo_addons/td_sale_cost@0976f05 |
| Модулі зв'язку з верстатами, СКУД, енергетикою й двором потребують обладнання конкретних виробників; у реальному впровадженні не перевірялись (демо-стенд, тестовий сервер) | обмеженість аналізу | П-01 | repo:todo_timur/factory3d/build/BUILD_STATUS.md@adce004 |
| П-01 — демо без клієнта: даних про сегмент, болі й вимоги реальних виробників немає; AIKB-проєкту немає; Fathom вимкнено DATA_POLICY | обмеженість аналізу | П-01 | repo:todo_timur/factory3d/README.md@adce004 |

## Для шлюзу: проєкти в цільовому сегменті

- Кількість (у сегменті: так): N = 0
- П-xx: немає
- Невідомо: П-01
- Виключені (інша галузь): немає
