# Технічний дизайн пакета «меблі» (A-08) — зміст

Пакет `mebli`, Odoo 19.0 CE (основа) + EE (мости), 2026-11-12. Поведінка й AC — `package/SPEC.md`; тут — **як** це влаштовано в Odoo (моделі `td.mebli.*`, поля `td_*`, права, подання, кнопки, cron, друк, обмін). Описано лише нове відносно стандарту Odoo 19 CE; стандартні поля названо з посиланням `файл:рядок` на вихідники 19.0 CE @ `40e9be2b` (`/home/user/odoo19/src`). Довідники скіла `docs/odoo19-довідник.md`, `docs/odoo-конвенції.md` у середовищі відсутні — звірка виконана за вихідниками (зауваження до скіла — у звіті кроку). EE не звірено (ВП-4).

## 1. Файли

| Файл | Що всередині | Модулі |
|---|---|---|
| `00-architecture.md` | перелік модулів (зріз / хвиля 2 / нові), граф залежностей, коробки й feature-групи, CE ↔ EE, версії й конвенції | усі |
| `security.md` | групи ролей, матриця доступу, `ir.rule`, multi-company, чутливі поля, юрособи ТОВ / ФОП | `td_mebli_base` + усі |
| `td_mebli_base.md` | параметри анкети на `res.company`, налаштування, шрифт PDF, міграція параметрів зрізу | `td_mebli_base` (новий) |
| `td_mebli_mrp.md` | специфікація замовлення, деталь, правила, імпорт CSV/Excel, шаблон мапінгу, норми й розцінки, завантаження, аналоги | `td_mebli_mrp` |
| `td_mebli_sale.md` | дати й прогноз, причина зсуву, етап дошки, графік оплат, ціна з розмірів, зміна замовлення, договір, візуалізація | `td_mebli_sale` |
| `td_mebli_measure.md` | замір-лист, ніші, техніка, запис на замір | `td_mebli_measure` |
| `td_mebli_cutting.md` | завдання розкрою (без оптимізатора), порізка в дистриб'ютора, перевірка за заміром, обрізки | `td_mebli_cutting` |
| `td_mebli_shop.md` | кіоск за PIN, крок якості, комплектувальний лист, етикетки й сканування | `td_mebli_shop` |
| `td_mebli_install.md` | акти й недоліки, етапи після «Виготовлено», контроль доплати й ручна позначка, денний план, нарахування | `td_mebli_install` |
| `td_mebli_claim.md` | рекламація на `repair.order`, повторне виготовлення, гарантія, платний ремонт | `td_mebli_claim` |
| `td_mebli_cost.md` | собівартість план ↔ факт, перевитрата | `td_mebli_cost` |
| `td_mebli_purchase.md` | ціна проти історії, імпорт прайсу | `td_mebli_purchase` |
| `td_mebli_dashboard_notify.md` | дашборд (12 карток), табло цеху, активності, листи, нагадування, брифінг (cron) | `td_mebli_dashboard`, `td_mebli_notify` |
| `td_mebli_hr_maint.md` | верстати ↔ дільниці й простій, табель з кіоску відвідувань | `td_mebli_maint`, `td_mebli_attendance` |
| `integrations.md` | обмін з BAS/BAF, курс НБУ, `l10n_ua` і ПДВ | `td_mebli_bas` (новий), `td_mebli_ua` |
| `td_mebli_multico.md` | монтаж від іншої юрособи (AI-14) | `td_mebli_multico` (новий, B) |
| `migration.md` | порядок імпорту майстер-даних A-13, дані на старті, конвертори й звірка | `td_mebli_migration` (новий) |
| `print-forms.md` | друковані форми QWeb-PDF | `td_mebli_sale`, `_shop`, `_install`, `_cutting` |
| `ee-bridges.md` | 6 мостів EE (контракт, не звірено) | `td_mebli_shopfloor`, `_quality`, `_fsm`, `_planning`, `_helpdesk`, `_sign` |
| `nfr.md` | продуктивність, мобільність і офлайн, безпека, бекапи, оновлення, експлуатація CE | — |
| `REVIEW.md` | рецензія tr-review (гейт A-08) | — |

## 2. AC без нашого коду (стандарт і конфіг — для A-12)

| AC | Що налаштувати (конфіг-пакет A-12 / дані A-13) | Стандарт Odoo 19 |
|---|---|---|
| AC-001 | CRM, тип зустрічі «Замір», замірники — користувачі з календарем | `addons/crm/models/calendar.py:26` (`opportunity_id`) |
| AC-004 | нагадування листом за 1 день для типу «Замір» | `addons/calendar/models/calendar_alarm.py:8` |
| AC-011 | виключення значень атрибутів виробів (B) | `addons/product/models/product_template_attribute_exclusion.py:7` |
| AC-019 | умови оплати з рядками-етапами (`td_milestone` — наш довідник) | `addons/account/models/account_payment_term.py:281-308` |
| AC-024 | маршрути MTO + «Купити» на замовних позиціях, ціни постачальників зі строком | `addons/stock/data/stock_data.xml:42`, `addons/purchase_stock/data/purchase_stock_data.xml:10` |
| AC-030 | шаблони листів `td_mebli_notify` (дані модуля) | `addons/mail/models/mail_template.py:19` |
| AC-043, AC-044 | товар-послуга «Монтаж» зі створенням задачі в проєкті «Монтажі» | `addons/sale_project/models/product_template.py:22` |
| AC-070 | причини втрат дільниць | `addons/mrp/models/mrp_workcenter.py:477` |
| AC-077 | кіоск відвідувань з PIN | `addons/hr_attendance/models/res_company.py:34` |
| AC-082 | резервування й поповнення (правила, MTO) | `addons/stock/models/stock_move.py:2064` (`_action_assign`) |
| AC-084 | аналіз закупівель | `addons/purchase/report/purchase_report.py:14` |
| AC-095 | проєкт «Монтажі», календар задач, бригади-виконавці | `addons/project/views/project_task_views.xml:829` |
| AC-116 | споживання «Дозволено з попередженням» у специфікаціях (генератор ставить сам) | `addons/mrp/models/mrp_bom.py:70` |
| AC-117 | онлайн-підпис пропозицій | `addons/sale/models/sale_order.py:112` (`require_signature`) |

## 3. Модель ↔ AC (нові `td.mebli.*` і ключові поля)

| Модель / поле | Модуль | AC |
|---|---|---|
| `td.mebli.measure`, `.niche`, `.appliance`; `td.mebli.measure.booking`, `.slot` | measure | AC-002, AC-003, AC-005…AC-010 |
| `td.mebli.part`, `td.mebli.part.rule`; `mrp.bom.td_*`; `product.template.td_*` | mrp | AC-012…AC-014, AC-045, AC-051, AC-052, AC-068 |
| `td.mebli.spec.import`, `td.mebli.import.template` | mrp | AC-045…AC-050 |
| `mrp.routing.workcenter.td_*`, `mrp.workcenter.td_capacity_hours`, `mrp.workorder.td_load_*` | mrp | AC-068, AC-069, AC-104 |
| `product.template.td_analog_ids`, `stock.move.td_analog_*` | mrp | AC-088 |
| `sale.order.td_forecast_date`, `td_delay_*`, `td_late_*`, `purchase.order.line.td_date_ready`, `res.partner.td_supplier_delay_avg` | sale | AC-022…AC-025, AC-083 |
| `sale.order.td_stage`, `td_stage_date` | sale, install | AC-063…AC-067 |
| `sale.order.line.td_width/height/depth`, `td_size_factor`, `td_planned_*` | sale | AC-015…AC-018 |
| `td.mebli.order.change` | sale | AC-118…AC-120 |
| `account.payment.term.line.td_milestone`, `sale.order.td_pay_*`, `td.mebli.pay.mark` | sale, install | AC-019…AC-021, AC-042 |
| `sale.order.td_design_image`; звіт договору | sale | AC-032…AC-034 |
| `td.mebli.cutting.job` (+ `.sheet`, `.placement`, `.offcut`), `stock.lot.td_*`, `td.mebli.measure.warning` | cutting | AC-026…AC-028, AC-053…AC-060 |
| `td.mebli.kiosk`, `mrp.workcenter.productivity.td_employee_id`, `hr.employee.td_pin_*` | shop | AC-071…AC-073 |
| `td.mebli.quality.check`, `mrp.workorder.td_quality_*` | shop | AC-074, AC-075 |
| `td.mebli.kit.line`, `stock.picking` (перевірка), звіти етикеток | shop | AC-061, AC-062, AC-091…AC-094 |
| `td.mebli.install.act`, `.defect`, `project.task.td_*` | install | AC-096…AC-103 |
| `td.mebli.accrual`, `td.mebli.accrual.reason`, майстер нарахування | install | AC-104…AC-108 |
| `repair.order.td_*`, `product.category.td_warranty_months` | claim, base | AC-080, AC-081, AC-110…AC-112 |
| `sale.order.td_cost_*`, `td_overconsumption` | cost | AC-114…AC-116 |
| `purchase.order.line.td_history_price…`, `td.mebli.price.import` | purchase | AC-085…AC-087 |
| `td.mebli.dashboard` (картки, табло) | dashboard | AC-079, AC-121…AC-123 |
| активності, шаблони, cron | notify | AC-029…AC-031, AC-124, AC-125 |
| `maintenance.equipment.td_workcenter_id`, `maintenance.request.td_downtime_*` | maint | AC-076 |
| `td.mebli.timesheet.export` | attendance | AC-078 |
| `td.mebli.bas.channel`, `.batch`, `.log`, `*.td_bas_code`, `account.move.td_bas_state` | bas | AC-039…AC-042, AC-078, AC-109 |
| `res.currency.rate.td_source`, cron НБУ | ua | AC-037, AC-038 |
| `sale.order.td_install_company_id`, `td_parent_order_id` | multico | AC-035 |
| `company_id` + `ir.rule` на td_-моделях; групи | base | AC-006, AC-018, AC-036, AC-115, AC-122 |
| `td.mebli.migration.check`, `.line`; конвертори | migration | AC-089, AC-090 |
| мости EE | `td_mebli_*` мости | AC-113, AC-126…AC-130 |

## 4. Вхід для наступних кроків
- **A-09 (анкета):** реєстр точок варіативності VP-01…VP-18 і службові `edition`, `contract_mode` — `SPEC.md` §11.
- **A-10 (ALLOCATION):** AC з треками — `SPEC.md` §5; модулі — `00-architecture.md` §1. VP кожного AC — хвіст «VP:» рядка трасування.
- **A-11 (код):** беклог — `SPEC.md` §7 «Розбіжності зі зрізом» (R-01…R-22) і «нове» в кожному файлі модуля.
- **A-12 (конфіг-пакет):** §2 цього файлу, параметри `td_mebli_base.md` §1, feature-групи `00-architecture.md` §3; VP → параметр — `SPEC.md` §11.1 (колонка «Де застосовується»).
- **A-13 (майстер-дані):** `migration.md` §1.
- **A-14 (гейти):** security-review — `security.md`; config-review — §2; track-convergence — `SPEC.md` §5–§6.
