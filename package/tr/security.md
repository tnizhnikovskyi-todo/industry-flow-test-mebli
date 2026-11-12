# Права доступу, ролі, правила записів, юрособи (ТОВ / ФОП)

Звірка: `ir.rule` — `odoo/addons/base/models/ir_rule.py:22-30` (поля `groups`, `domain_force`, `perm_*`), змінна `company_ids` у домені — `:49`; групи — `odoo/addons/base/models/res_groups.py:36` (`privilege_id`), `:69` (`implied_ids`); компанії користувача — `odoo/addons/base/models/res_users.py:245-247` (`company_id`, `company_ids`); перевірка узгодженості компаній зв'язків — `_check_company_auto` / `check_company=True` (`odoo/orm/models.py:451`). AC: AC-006, AC-018, AC-021, AC-036, AC-064, AC-099, AC-106, AC-115, AC-122.

## 1. Групи

Привілей `res.groups.privilege` «Меблі» (модуль `td_mebli_base`). Стандартні групи — без змін; наші групи додають доступ до `td.mebli.*` і видимість полів.

| Група (`td_mebli_base.`) | Назва | Включає (`implied_ids`) | Для ролі |
|---|---|---|---|
| `group_measurer` | Меблі: Замірник | `base.group_user` | ROLE-09 |
| `group_technologist` | Меблі: Технолог | `mrp.group_mrp_user`, `stock.group_stock_user` | ROLE-01 |
| `group_shop_master` | Меблі: Майстер цеху | `mrp.group_mrp_user`, `hr.group_hr_user` (лише читання працівників — через правила) | ROLE-03 |
| `group_installer` | Меблі: Монтажник | `project.group_project_user` | ROLE-10 |
| `group_service` | Меблі: Сервіс | `stock.group_stock_user` (права `repair`) | ROLE-10 (сервіс) |
| `group_finance` | Меблі: Фінансист | `account.group_account_invoice` | ROLE-06 |
| `group_director` | Меблі: Керівник | `group_finance`, `sales_team.group_sale_salesman_all_leads`, `mrp.group_mrp_user` (читання), `project.group_project_user` | ROLE-08 |
| `group_kiosk` | Меблі: Кіоск цеху | `base.group_user` | пристрій-планшет, ТВ |
| `group_margin_view` | Меблі: Бачить маржу | — | ставиться автоматично за параметром «Менеджер бачить маржу» (AC-018) |
| `group_feature_*` | функції коробки B | — | §3 `00-architecture.md` |

Група зрізу `td_mebli_dashboard.group_td_mebli_director` переходить у `td_mebli_base.group_director` (міграція `migrations/19.0.1.1.0/post-migrate.py`: користувачі зі старої групи отримують нову).

## 2. Матриця доступу до td_-моделей (`ir.model.access.csv`)

R — читання, W — запис, C — створення, D — видалення.

| Модель | Замірник | Менеджер | Технолог | Майстер цеху | Комірник | Монтажник | Сервіс | Фінансист | Керівник | Кіоск |
|---|---|---|---|---|---|---|---|---|---|---|
| `td.mebli.measure`, `.niche`, `.appliance` | RWCD (свої) | RWC | R | R | — | R | R | — | R | — |
| `td.mebli.part`, `td.mebli.part.rule` | — | R | RWCD | R | R | R | R | R | R | R |
| `td.mebli.import.template` | — | — | RWCD | — | — | — | — | — | R | — |
| `td.mebli.order.change` | — | RWC | R | R | — | — | — | R | RW | — |
| `td.mebli.cutting.job` (+ `.sheet`, `.placement`) | — | R | RWCD | RW | RW | — | — | R | R | — |
| `td.mebli.kit.line` | — | R | R | R | RWCD | R | — | — | R | — |
| `td.mebli.quality.check` | — | — | R | RW | — | — | R | — | R | C (через кіоск) |
| `td.mebli.install.act`, `.defect` | — | R | — | — | — | RWC (своїх виїздів, чернетка) | R | R | R | — |
| `td.mebli.accrual` | — | — | — | RWC (свої дільниці, чернетка) | — | R (свої) | — | RWCD | RW (підтвердження) | — |
| `td.mebli.pay.mark` | — | R | — | — | — | R | — | RWC | RWC | — |
| `td.mebli.bas.batch`, `.log` | — | — | — | — | — | — | — | RWC | R | — |
| `td.mebli.dashboard` (клієнтська дія) | — | — | — | — | — | — | — | — | R | R (лише табло) |
| `repair.order` (поля `td_`) | — | R | — | R | — | RW | RWC | R | R | — |

## 3. Правила записів (`ir.rule`)

**Multi-company (усі td_-моделі із записами):** поле `company_id = fields.Many2one('res.company', required=True, index=True, default=lambda self: self.env.company)` і глобальне правило `[('company_id', 'in', company_ids)]` (глобальне — без `groups`; `company_ids` — дозволені й обрані компанії, `ir_rule.py:49`). `_check_company_auto = True` і `check_company=True` на many2one до записів інших компаній.

| Модель | Звідки `company_id` | Стан у зрізі | Дія A-11 |
|---|---|---|---|
| `td.mebli.measure` | замовлення / нагода | є, правило є | — |
| `td.mebli.accrual` | компанія користувача / акта | є, правило є | — |
| `td.mebli.cutting.job` | компанія МО | поле є, правила немає | додати правило |
| `td.mebli.part` | related `bom_id.company_id`, `store=True` | немає | додати related + правило |
| `td.mebli.kit.line` | related `order_id.company_id`, `store=True` | немає | додати |
| `td.mebli.quality.check` | related `workorder_id.company_id`, `store=True` | немає | додати |
| `td.mebli.order.change` | related `order_id.company_id`, `store=True` | немає | додати |
| `td.mebli.install.act` / `.defect` | related `task_id.company_id` / `act_id.company_id`, `store=True` | немає | додати |
| `td.mebli.pay.mark`, `td.mebli.bas.*`, `td.mebli.import.template` | компанія документа / користувача | нові | з першого коміту |

**Рольові правила:**

| Правило | Модель | Групи | Домен | Права |
|---|---|---|---|---|
| Замірник — свої заміри | `td.mebli.measure` | `group_measurer` | `[('measurer_id', '=', user.id)]` | R W C D |
| Продаж — заміри своїх замовлень/нагод | `td.mebli.measure` | `sales_team.group_sale_salesman` | `['|', ('order_id.user_id', '=', user.id), ('lead_id.user_id', '=', user.id)]` | R W C |
| Усі заміри | `td.mebli.measure` | `sales_team.group_sale_salesman_all_leads`, `mrp.group_mrp_user`, `group_director` | `[(1, '=', 1)]` | R |
| Акт — як його виїзд | `td.mebli.install.act` | `project.group_project_user` | дзеркало правила видимості задач `project.task_visibility_rule` (у зрізі) | R |
| Бригада редагує чернетку | `td.mebli.install.act` | `group_installer` | `[('task_id.user_ids', 'in', user.id), ('state', '=', 'draft')]` | W C |
| Нарахування — своє | `td.mebli.accrual` | `group_installer` | `[('employee_id.user_id', '=', user.id)]` | R |
| Нарахування — підтверджене не змінюється | `td.mebli.accrual` | усі, крім `group_director` | `[('state', '=', 'draft')]` | W D |
| Закупівлі моїх замовлень (зріз) | `purchase.order`, `.line` | `sales_team.group_sale_salesman` | за `reference_ids.sale_ids.user_id` (`td_mebli_sale/security/purchase_security.xml`) | R |
| Ручна позначка оплати | `td.mebli.pay.mark` | `group_finance`, `group_director` | `[(1, '=', 1)]` | R W C |

**Робітник цеху без користувача.** Працівник `hr.employee` (поле PIN — `addons/hr/models/hr_employee.py:211`) не має `res.users`; планшет працює під користувачем `group_kiosk`. Кіоск не дає читати ставки й нарахування інших (діалог показує лише своє після PIN). Лічильник невдалих PIN — поля працівника `td_pin_fail_count` (Integer, `groups='hr.group_hr_user'`), `td_pin_locked_until` (Datetime) (AI-A08-12, AC-071).

## 4. Чутливі поля (атрибут `groups` у моделі)

| Поле | `groups` |
|---|---|
| `sale.order.line.td_planned_material_cost`, `td_planned_operation_cost`; `sale.order.td_cost_*`, `td_margin_*`; стандартні `margin`, `margin_percent` у поданнях пакета | `td_mebli_base.group_margin_view,td_mebli_base.group_finance,sales_team.group_sale_manager` |
| `mrp.routing.workcenter.td_piece_rate` | `mrp.group_mrp_manager,td_mebli_base.group_finance` |
| `td.mebli.accrual.amount` (у чужих рядках) | правило §3 |
| `purchase.order.line.td_history_price`, `td_overpay` | `purchase.group_purchase_user,td_mebli_base.group_director` |

## 5. Юрособи (C-03, AI-14)

- Одна компанія на замовлення (`sale.order.company_id`, `addons/sale/models/sale_order.py:61`); рядки не розщеплюються.
- Монтаж від іншої юрособи — окреме замовлення-послуга в компанії ФОП (`td_mebli_multico.md`).
- Параметри анкети — поля `res.company` (AI-A08-04), тож кожна юрособа має свій режим договору, контроль доплати, % бригаді.
- Обмін BAS — пакет на кожну компанію (`integrations.md`).
- EE: увімкнення кількох компаній на EE Standard переводить на план Custom (FM §4.5) — повідомити в продажу (не технічне обмеження).
