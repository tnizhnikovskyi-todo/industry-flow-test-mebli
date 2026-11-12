# `td_mebli_cost` — собівартість замовлення план ↔ факт

**Призначення.** S-11 (F-14, F-52 — звіт перевитрат). Основа `ToDo-готовий` REUSE-01 `td_sale_cost` — **як ідея** (код репозиторію REUSE-01 у сесіях не читався; AI-A08-08, R-13). Коробка A. AC: AC-114…AC-116.
**Звірка:** `addons/sale_margin/models/sale_order.py:10-11` (`margin`, `margin_percent`); розрахунок як у стандартному огляді МО `addons/mrp/report/mrp_report_mo_overview.py:227` (спожите × `standard_price`), `:385` (години × `costs_hour`); `addons/mrp/models/mrp_workcenter.py:41` (`costs_hour`); `addons/mrp/models/mrp_production.py:177` (`state`); аналітика МО (CE, перевірка №13) — `addons/project_mrp_account/models/mrp_production.py:10-16` — **необов'язкова** джерело.

## 1. Поля `sale.order` (усі compute, без store; `groups` — фінансист, керівник, `group_margin_view`)

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Планова собівартість (`td_cost_plan`) | monetary | `amount_untaxed − margin` (`sale_margin`) | без ПДВ |
| Факт матеріалів (`td_cost_material`) | monetary | спожиті рухи МО замовлення × `standard_price` на дату | — |
| Факт робіт (`td_cost_work`) | monetary | тривалість рядків часу × `costs_hour` дільниці | — |
| **Порізка (`td_cost_cutting`)** | monetary | рядки закупівель послуги порізки МО замовлення (`td.mebli.cutting.job.purchase_id`) | **нове** (стаття REUSE-01) |
| **Відрядна й % бригаді (`td_cost_labour`)** | monetary | `td.mebli.accrual` замовлення (підтверджені) | **нове**; не дублює `td_cost_work`, якщо компанія веде вартість години без зарплати (параметр звіту «Враховувати відрядну замість години») |
| Факт (`td_cost_fact`), Маржа факт (`td_margin_fact`, `td_margin_fact_pct`), Маржа план % (`td_margin_plan_pct`), Відхилення % (`td_cost_deviation_pct`) | monetary / float | похідні | — |
| Виробництво завершено (`td_cost_has_fact`) | boolean | усі МО `done` | інакше «Факту ще немає» (AC-114) |
| **Перевитрата (`td_overconsumption`)** | boolean compute, search | МО з фактичним споживанням > кількості специфікації (стандартний механізм `consumption = 'warning'`) | **нове**; фільтр «Перевитрата» (AC-116) |

## 2. Подання
Меню «Облік / Продажі → Звіти → Собівартість план ↔ факт» — `<list>` замовлень з колонками вище, підсумки (`sum`, маржа % зважено), `<pivot>`; кнопка «Відкрити відхилення» — МО замовлення; права — `security.md` §4 (AC-115). Залежність модуля — `td_mebli_sale`, `td_mebli_cutting`, `td_mebli_install` (для статей) (граф — `00-architecture.md` §2).
