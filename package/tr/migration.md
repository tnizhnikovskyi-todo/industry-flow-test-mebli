# Міграція й майстер-дані (вхід для A-13 і B-06), `td_mebli_migration`

AC: AC-089, AC-090; довідники — передумови для AC-011, AC-013, AC-015, AC-019, AC-024, AC-070, AC-085, AC-104, AC-107, AC-110. Джерела: `research/BOX.md` §3 (довідники), §4 (дані на старті), AI-13 (формати без зразків).

## 1. Майстер-дані — порядок імпорту CSV-шаблонів A-13

Стандартний імпорт Odoo (`base_import`, `addons/base_import/models/base_import.py:177`); наші поля — у тих самих шаблонах. Порядок — за залежностями.

| № | Шаблон A-13 | Модель | Наші поля / моделі | Хто заповнює | Коробка |
|---|---|---|---|---|---|
| 1 | Компанії й параметри | `res.company` | `td_contract_mode`, `td_payment_control`, `td_crew_pct`, … (`td_mebli_base.md` §1) | конфіг-пакет A-12 з `answers.yaml` | A |
| 2 | Одиниці (лист, м², п. м, шт, комплект) | `uom.uom` | — | конфіг | A |
| 3 | Категорії товарів і гарантія | `product.category` | `td_warranty_months` (порожньо до юриста) | клієнт | A |
| 4 | Плити й декори, кромка, фурнітура | `product.template` / `product.product` | `td_material_kind`, `td_sheet_*_mm`, `td_thickness_mm`, `td_waste_pct`, `td_matches_board_id`, `td_edge_thickness`, `td_bas_code` | клієнт (з BAS — зі збереженням коду) | A |
| 5 | Замовні позиції | `product.template` (маршрути MTO + «Купити») | — | клієнт | A |
| 6 | Ціни постачальників | `product.supplierinfo` | — (або майстер прайсу F-59) | клієнт | A |
| 7 | Вироби й модулі, атрибути, виключення | `product.template`, `product.attribute`, `product.template.attribute.exclusion` | `td_is_parametric`, розміри, `td_component_role`, `td_component_product_id` | клієнт / технолог | A (виключення — B) |
| 8 | Правила деталей | `td.mebli.part.rule` | — | технолог | A |
| 9 | Дільниці, операції, норми, розцінки | `mrp.workcenter`, `mrp.routing.workcenter` (у шаблонах специфікацій `mrp.bom`) | `td_time_basis`, `td_time_rate`, `td_piece_rate`, `td_quality_point` (B) | технолог | A |
| 10 | Причини втрат (простої) | `mrp.workcenter.productivity.loss` | — | конфіг | A |
| 11 | Обладнання ↔ дільниці | `maintenance.equipment` | `td_workcenter_id` | клієнт | A |
| 12 | Працівники, PIN, бригади | `hr.employee` | `pin` (стандарт), `td_bas_code` | клієнт | A |
| 13 | Умови оплати з етапами | `account.payment.term` / `.line` | `td_milestone` | конфіг / клієнт | A |
| 14 | Причини премій і штрафів | `td.mebli.accrual.reason` | — | клієнт | A |
| 15 | Теги рекламацій | `repair.tags` | — | конфіг | A |
| 16 | Шаблони мапінгу імпорту | `td.mebli.import.template` | — | технолог (після зразків CAD) | A |
| 17 | Клієнти | `res.partner` | `td_bas_code` | менеджер / B-06 | A |

## 2. Дані на старті (BOX §4)
- **Коробка A:** клієнти з відкритими замовленнями й гарантією; відкриті **не запущені** замовлення (≤ 50 [пропозиція]) — нові `sale.order` з поточною версією специфікації, отримані оплати одним платежем на дату старту; залишки на одну дату (стандартне коригування); список змонтованих на гарантії (замовлення — дата акта — виріб) для рекламацій. Замовлення в цеху чи на монтажі — доводяться в старій системі.
- **Коробка B, C:** повна міграція (D-10) — довідники, відкриті й закриті замовлення, залишки, історія з BAS/BAF і бібліотек БАЗИС.

## 3. `td_mebli_migration` (новий)
- **Конвертори** (коробка B): Python-скрипти `scripts/convert_bas.py`, `scripts/convert_bazis.py` — читають вивантаження (формати — після зразків, AI-13, ВП-1, ВП-3) і пишуть CSV-шаблони §1; запуск — крок B-06 (`client-data-migrator`) на тестовій базі, не на проді.
- **Звірка** (коробки A, B): модель `td.mebli.migration.check` (`name`, `company_id`, `date`, `state`: чернетка / розбіжність / звірено / пояснено) і рядки `td.mebli.migration.check.line` (`metric`: сума передоплат відкритих замовлень / кількість відкритих замовлень / залишок товару; `value_source` — float, ввід з джерела; `value_odoo` — float compute; `diff` — compute; `note`). Стан «звірено» — лише при нульовій різниці або заповненому поясненні керівника (AC-090). Звіт звірки — `<list>` і PDF.
- Зовнішні коди BAS зберігаються в `td_bas_code` (обмін зіставляє документи).

## 4. Шаблони пакета для клієнта (A-18)
`package/templates/migration-plan.md` (A-18) посилається на §1–§3; цей файл — джерело порядку імпорту для A-13.
