# AC-COVERAGE-G3 — монтаж, рекламація, собівартість, дашборд (A-11, G3)

Гілка `flow/A-11-test`, після злиття G0+G1+G2+G4 (HEAD `5529dc0`). Модулі групи: `td_mebli_install`, `td_mebli_claim`,
`td_mebli_cost`, `td_mebli_dashboard` (версії підняті до `19.0.1.1.0`). Прогін: установка в чисту базу + оновлення з
попередньої версії (`19.0.1.0.0`) з `migrations/`; тести своїх модулів на чистій базі
(`test-mebli-a11g3-c`, порт 8173) — **61 тест, 0 failed, 0 error** (install 56, claim 16, cost 6, dashboard 17 — у
лічильнику модуля є й тести залежностей). Залежні `td_mebli_notify`/`td_mebli_demo`: 18 тестів, 1 failed —
`td_mebli_demo/tests/test_scenario.py::test_scenario` (лоти розкрою G2; падає й без коду G3 на HEAD — не G3). Тексти помилок і чисел — дослівно за SPEC §4.3/§4.10/§4.11/§4.18;
переклади uk — у `i18n/uk.po` кожного модуля (перевірено `uk_UA` у тестах нещасливих шляхів).

## Покриття AC

| AC | Стан | Реалізація | Тест |
|---|---|---|---|
| AC-020 | done | Контроль доплати VP-06 читається з поля `res.company.td_payment_control` (не `ir.config_parameter`); `warn` — банер + запис у чаті замовлення, дія виконується; `block` — UserError «Монтаж заблоковано: не отримано доплату <сума>. Зверніться до менеджера», стан не змінюється | `td_mebli_install/tests/test_g3.py::TestPaymentG3.test_ac_020_warn_posts_in_the_chatter`, `test_ac_020_block_error_of_spec`; `test_payment.py::test_warn_by_default_block_by_parameter` |
| AC-021 | done | Модель `td.mebli.pay.mark` (нова, її чекав G4 для AC-042); «Оплату підтверджено вручну» (`group_finance`); без причини — ValidationError «Вкажіть причину ручної позначки оплати»; `_td_paid_amount` враховує непорожні позначки; менеджер і бригадир дії не мають; запис у чат; `cancelled` для AC-042 | `test_g3.py::TestPaymentG3.test_ac_021_manual_mark_counts_as_paid`, `test_ac_021_reason_required_error_of_spec`, `test_ac_021_manager_and_crew_have_no_action` |
| AC-080 | done | «Повторне виготовлення» на деталь: МО з однодетальної специфікації (`product_remake_part`, плати й операції деталі), `origin` = номер рекламації; на виріб — як раніше | `td_mebli_claim/tests/test_claim.py::TestClaim.test_ac_080_remake_of_the_part`, `test_claim_on_the_order_and_remake` |
| AC-081 | done | Без деталі й виробу — UserError «Оберіть деталь або виріб для повторного виготовлення», МО не створюється | `test_claim.py::TestClaim.test_ac_081_no_part_no_product` |
| AC-100 | done | Поле `photo_consent`; дія «У фотоархів» (і на підписаному акті — read-only для бригади); без згоди — UserError/ValidationError «Немає згоди покупця на публікацію фото»; фільтр «Фотоархів» | `test_g3.py::TestActG3.test_ac_100_photo_archive_needs_the_consent` |
| AC-102 | done | У звіті акта позначка «Шаблон до перевірки юристом» за `company.td_legal_checked`; клас `td_mebli_report` (AC-N.06) | `test_g3.py::TestActG3.test_ac_102_lawyer_mark_until_checked` |
| AC-103 | done | VP-15 `td_crew_base`: «За фінальним актом» (етап = 0, «Закрито» лише після фінального) і «За етапами» (кожен акт — свою частку `stage_pct`, фінальний — решту) | `test_g3.py::TestActG3.test_ac_103_two_visits_by_the_final_act`, `test_ac_103_two_visits_by_stages` |
| AC-104 | done | % бригаді VP-14 `td_crew_split`: порівну або за годинами `crew_line_ids`; `td_crew_pct` компанії як дефолт акта; ідемпотентність за `act_id` | `test_g3.py::TestAccrualG3.test_ac_104_crew_percent_equally`, `test_ac_104_crew_percent_by_time`, `test_ac_104_default_percent_of_the_company` |
| AC-105 | done | Майстер «Нарахувати за період» (`td.mebli.accrual.wizard`); операції без розцінки — рядок не створюється, підсумок «Без розцінки: N операцій» зі списком | `test_g3.py::TestNoPieceRateG3.test_ac_105_operation_without_piece_rate` |
| AC-106 | done | Правила: працівник бачить лише свої нарахування; підтверджене — read-only; скасування підтвердженого лише керівником (`mrp_manager`/`account_manager`) з причиною (`action_td_cancel`) | `test_g3.py::TestAccrualG3.test_ac_106_own_lines_and_confirmed_read_only` |
| AC-107 | done | Довідник `td.mebli.accrual.reason`; майстер (`mrp.group_mrp_user`) додає премію/штраф лише працівникам своєї дільниці (`department_id.manager_id`/`parent_id`) у чернетці; автор у `author_id` | `test_g3.py::TestAccrualG3.test_ac_107_master_adds_bonus_in_his_section` |
| AC-108 | done | Премія/штраф без причини — ValidationError «Вкажіть причину премії або штрафу» (ORM перед SQL-обмеженням) | `test_g3.py::TestAccrualG3.test_ac_108_bonus_without_reason` |
| AC-110 | done | «Прострочено» понад `company.td_claim_overdue_days` (VP-13) від `create_date`, не від `schedule_date`; `search` для фільтра; смарт-кнопка «Рекламації» | `test_claim.py::TestClaim.test_ac_110_overdue_by_the_parameter_of_the_company` |
| AC-111 | done | «Гарантія до» = дата фінального акта + `product.category.td_warranty_months`; порожньо — `td_warranty_unset` і «Гарантійний строк не задано», `under_warranty` вручну; `td_mebli_claim.warranty_months` зрізу більше не читається | `test_claim.py::TestWarranty.test_ac_111_warranty_of_the_category`, `test_ac_111_term_not_set`, `test_after_warranty_the_customer_pays` |
| AC-112 | done (G2-зріз) | Платний ремонт — стандарт `repair`→`sale` (`action_create_sale_order`), `td_after_warranty` знімає `under_warranty` | `test_claim.py::TestWarranty.test_after_warranty_the_customer_pays` |
| AC-114 | done | Факт собівартості: матеріали, години, **порізка** (`td_cost_cutting` — закупівлі послуги порізки МО), **відрядна+% бригаді** (`td_cost_piece`/`td_cost_crew` з підтверджених `td.mebli.accrual`); параметр `td_cost_piecework` (відрядна замість годин); незавершені МО — «Факту ще немає» | `td_mebli_cost/tests/test_cost.py::TestCost.test_plan_and_actual`, `test_ac_114_cutting_piecework_and_crew` |
| AC-115 | done | `groups` на полях факту (`group_finance`) і плану (`group_margin_view`/finance/sale_manager); меню й сторінка форми — `group_finance` | `test_cost.py::TestCost.test_ac_115_cost_only_for_the_finance` |
| AC-116 | done | Поле `td_overconsumption` (compute+search) порівнює спожите з розкладеною специфікацією; фільтр «Перевитрата» у звіті S-11 | `test_cost.py::TestCost.test_ac_116_overconsumption_filter` |
| AC-121 | done | 12-та картка «Невідповідності якості» (`group_feature_quality`): `td.mebli.quality.check` `result='fail'` — і крок якості, і брак (AC-073, `kind='scrap'`); у коробці A — 11 карток | `td_mebli_dashboard/tests/test_g3.py::TestDashboardG3.test_ac_121_twelfth_card_of_the_quality_in_box_b` |
| AC-122 | done | Меню «Дашборд керівника» — `group_td_mebli_director` (включає `group_finance`, `sale_salesman_all_leads`, `mrp.group_mrp_user`, `project.group_project_user`, `stock.group_stock_user` за `security.md` §1 — щоб кожна картка відкривала свої записи); `get_data` — AccessError для не-керівника; міграція скидає старі групи меню | `test_dashboard.py::test_access_is_limited_to_the_director`; `test_g3.py::test_ac_122_menu_and_finance_of_the_director` |
| AC-123 | done | Порожні дані — «Немає даних»/0, без ділення на нуль (`_no_data`) | `test_g3.py::TestDashboardG3.test_ac_123_empty_data`; `test_dashboard.py::test_cards_of_the_a_box` |
| AC-132 | done | «Запланувати виїзд» з рекламації: `project.task` у проєкті монтажів (`td_visit_kind='service'`, без акта/контролю доплати), `td_claim_id`, адреса; видно в календарі й денному плані | `test_claim.py::TestClaimVisit.test_ac_132_plan_a_visit`, `test_ac_132_order_without_installation` |
| AC-134 | done | QWeb «Відомість нарахувань» за працівниками й видами з причинами, підсумками, місцем підпису; лише підтверджені; клас `td_mebli_report` | `test_g3.py::TestAccrualG3.test_ac_134_accruals_sheet` |

## Хвости та міжгрупові залежності (закрито)
- **AC-021 `td.mebli.pay.mark`** — зроблено першою, G4 бере її для AC-042 (поле `cancelled`: обмін ставить при надходженні оплати).
- **AC-121 12-та картка** — отримує брак від G2 (`td.mebli.quality.check.kind='scrap'`, коміт `0dab06b`); картка рахує `result='fail'` незалежно від `kind`.
- **Зсув дати при порізці** — ключ `td_delay_reason`/дашборда переведено на `'distributor'` (було `'cutting'`) за хвостом G2.
- **Картка «Застряглі»** (хвіст G1) — читає збережене `sale.order.td_is_stuck` (VP-10 компанії, лише підтверджені), без власного підрахунку й константи.
- **AC-042 хук скасування позначок** — тіло хука `_td_after_bas_payment` лежить у `td_mebli_bas` (G4, не правлю): там треба один рядок
  `invoice.line_ids.sale_line_ids.order_id._td_cancel_pay_marks()`. Метод `sale.order._td_cancel_pay_marks()` (G3, ідемпотентний,
  ставить `cancelled`, запис у чат) — тест `td_mebli_install/tests/test_g3.py::TestPaymentG3.test_ac_042_cancel_marks_on_bas_payment`.
  Доки рядка немає — позначку знімає фінансист вручну.
- **Демо (`td_mebli_demo`, завершальний крок сесії):** `full.py:223` створює акт з `photo_archive: True` без `photo_consent` — тепер
  ValidationError (AC-100); треба додати `'photo_consent': True`. Демо спирається на `crew_pct` 5 % явно — ок; дефолт акта тепер
  `company.td_crew_pct` (0).
- **AC-073** (цех, G2) — сам кіоск «Брак» у модулі G2; тут лише читання для картки.

## Поля даних (нові td_; аналог у стандарті CE 19 або причина)

| Поле / модель | Тип | Модуль | Аналог / причина |
|---|---|---|---|
| `td.mebli.pay.mark` (order_id, company_id, amount, reason, user_id, date, cancelled) | модель | install | немає (ручна позначка оплати до обміну BAS) |
| `sale.order.td_pay_mark_ids` | o2m | install | — |
| `sale.order.td_pay_control` | тепер з `company.td_payment_control` (VP-06) | install | заміна `ir.config_parameter` зрізу |
| `project.task.td_visit_kind` (`install`/`service`) | selection | install | немає (виїзд-сервіс за рекламацією без акта) |
| `td.mebli.install.act.company_id` | related store | install | multi-company правило (`security.md` §3) |
| `td.mebli.install.act.photo_consent` | boolean | install | немає (AC-100, юр. форма — ВП-2) |
| `td.mebli.install.act.crew_base` (related), `stage_pct` | selection/float | install | VP-15 поділ % за етапами |
| `td.mebli.install.act.crew_line_ids` / `td.mebli.install.act.crew` (user_id, hours) | o2m / модель | install | VP-14 поділ % бригаді за годинами |
| `td.mebli.install.defect.company_id` | related store | install | multi-company |
| `td.mebli.accrual.reason` (name, kind, default_amount, company_id, active) | модель | install | AC-107 довідник причин (char зрізу → `reason` «коментар») |
| `td.mebli.accrual.reason_id`, `author_id`, `cancel_reason`; стан `cancel` | m2o/m2o/char/selection | install | AC-106/107/108 |
| `td.mebli.accrual.wizard`, `td.mebli.accrual.cancel` | TransientModel | install | AC-104/105/106 майстри |
| `repair.order.td_visit_task_id` | m2o readonly | claim | AC-132 задача-виїзд |
| `repair.order.td_warranty_unset`, `td_warranty_note` | boolean/char compute | claim | AC-111 строк категорії порожній |
| `repair.order.td_warranty_end`, `td_after_warranty` | тепер store, зі строку категорії | claim | заміна `ir.config_parameter` зрізу |
| `repair.order.td_overdue` | +`search` | claim | AC-110 фільтр |
| `project.task.td_claim_id` | m2o readonly | claim | AC-132 |
| `product.template product_remake_part` | дані | claim | AC-080 товар МО повторної деталі |
| `res.company.td_cost_piecework` | boolean | cost | AC-114 параметр звіту |
| `sale.order.td_cost_cutting`, `td_cost_piece`, `td_cost_crew`, `td_cost_labour`, `td_cost_status` | compute | cost | AC-114 статті факту |
| `sale.order.td_overconsumption` | boolean compute+search | cost | AC-116 |
| поля `td_cost_*`/`td_margin_fact*` отримали `groups` | — | cost | AC-115 |
| `td_mebli_dashboard.group_td_mebli_director` `implied_ids` += `group_finance` | — | dashboard | AC-115/021/122: керівник = права фінансиста |

## Рішення AI з ризиком
| # | Рішення | Ризик |
|---|---|---|
| G3-1 | VP-14 «За часом» бере години з нового `crew_line_ids` акта (рядки створюються з бригади при `create`); якщо години не введено — ділиться порівну | якщо бригадир не заповнить години, «За часом» = «Порівну» без попередження |
| G3-2 | AC-116 «Перевитрата» рахується розкладанням специфікації (`bom.explode`) і порівнянням зі спожитим; складені специфікації (фантоми) — за розкладеними рядками | глибокі фантоми/субспецифікації не перевірено на складних прикладах; тест — проста специфікація |
| G3-3 | AC-134/AC-102 звіти отримали клас `td_mebli_report` (AC-N.06); PDF малює web-шрифт контурами (без текстового шару) — як рішення G0-2 | пошук тексту в PDF акта/відомості не працює (інфраструктура C-00) |
| G3-4 | `td.mebli.pay.mark` рахується як «отримано» поряд із рахунками; задвоєння при приході оплати обміном знімає G4 через `cancelled` (AC-042) | до реалізації AC-042 ручну позначку знімає людина |
| G3-5 | Міграція `td_mebli_dashboard/19.0.1.1.0` скидає `group_ids` меню (menuitem `groups=` на оновленні — адитивний, лишав старі групи → дашборд був видимий усім) | якщо меню переозброять вручну після оновлення — міграція не повторюється (разова) |
| G3-6 | `td_mebli_install/19.0.1.1.0/pre-migrate` видаляє старе подання налаштувань зрізу (поле `td_mebli_payment_control` зникло) до оновлення | подання відтворюється новим з `td_mebli_base`; якщо хтось успадкував старий xmlid — зламається (нема таких у пакеті) |
| G3-7 | AC-105 список операцій без розцінки — текст (не посилання): у майстра немає прав виробництва відкрити МО | неклікабельно; достатньо для підсумку |
| G3-8 | Група керівника дашборда включає читання виробництва, проєкту, складу й усіх продажів (`security.md` §1), а не лише фінансиста — без цього картка «Завантаження» падала AccessError на `mrp.workcenter.productivity` (`td_worker_names` у списку планшета G2 без sudo) | керівник бачить меню виробництва/проєкту; група `td_mebli_base.group_director` з ТР ще не створена — перенос xmlid пізніше (AC-N.04) |
| G3-9 | Поділ «Застряглих» — за датою зміни етапу дошки (`td_is_stuck` G1), а не за рухом МО як у зрізі | інше визначення «руху», ніж у зрізі; відповідає AC-067 |
| G3-10 | Скасування підтвердженого нарахування — `mrp.group_mrp_manager` або `account.group_account_manager` («керівник»); `td_mebli_base.group_director` з ТР ще немає | коли з'явиться група керівника — замінити `CANCEL_GROUPS` |

## Що лишилось (не в обсязі G3)
- AC-042 (G4) — бере `td.mebli.pay.mark` і знімає `cancelled`.
- AC-109, AC-113, AC-126–130 — мости/BAS (G4).
- Повноту перекладу всіх `uk.po` і зведення у `CHECKS.md` — A-14.
