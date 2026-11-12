# `td_mebli_cutting` — розкрій, порізка в дистриб'ютора, перевірка за заміром, обрізки

**Призначення.** S-04 (F-05, F-11, F-28, F-30, F-62). Коробка A: завдання розкрою на одне МО, порізка в дистриб'ютора, перевірка за заміром; B: пакет кількох МО (`group_feature_cutting_batch`), ділові обрізки (`group_feature_offcut`). AC: AC-026…AC-028, AC-053…AC-060.
**Звірка:** `addons/purchase/models/purchase_order_line.py:25` (`date_planned`); `addons/product/models/product_supplierinfo.py:30` (`price`), `:51` (`delay`); `addons/stock/models/stock_lot.py:25` (`stock.lot`); `addons/mrp/models/mrp_bom.py:89`; субпідряд `addons/mrp_subcontracting` не підходить (деталі не є товарами складу — PLAN «Модель даних»). PLAN.md: `td.mebli.cutting.job/.sheet/.placement/.offcut`, `stock.lot.td_*`, `td.mebli.cutting.job.purchase_id/distributor_id/return_date`.

## 1. Завдання розкрою (`td.mebli.cutting.job`, `mail.thread`) — зріз + доробки

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Номер (`name`) | char, readonly | `ir.sequence` (`РЗ/%(year)s/`) | required |
| Стан (`state`) | selection: чернетка / відправлено / результат / закрито | кнопки | — |
| Компанія (`company_id`) | many2one | компанія МО | required; **правило multi-company — нове** (R-03) |
| Виробничі замовлення (`production_ids`) | many2many `mrp.production` | вибір | `check_company=True`; constraint: один матеріал плити (AC-058); >1 МО — лише з `group_feature_cutting_batch` |
| Деталі (`part_ids`), Штук (`part_count`) | many2many compute | деталі МО | деталь зберігає МО й замовлення (AC-057) |
| Аркуші (`sheet_ids`) | one2many `td.mebli.cutting.sheet` | результат | — |
| Пропил, мм (`kerf_mm`), Обрізка краю (`trim_mm`), Мін. обрізок (`min_offcut_mm`) | integer | default з компанії (`td_min_offcut_mm`) | — |
| Джерело результату (`result_source`) | selection: **`imported` «Імпорт з програми розкрою» / `manual` «Вручну»** | — | значення `simulated` і оптимізатор (`optimizer.py`, `sheet_map.py`) **вилучаються з модуля** (AI-A08-15, R-09); імітація лишається в `td_mebli_demo` |
| Відхід, % (`waste_pct`) | float compute | аркуші | KPI 10 (лише свій розкрій з результатом) |
| Файл розкрою (`export_attachment_id`) | many2one `ir.attachment`, readonly | «Передати на розкрій» | CSV деталей (AC-053) |
| **Версія специфікації (`bom_version`)** | char, readonly | `mrp.bom.td_version` під час відправлення | **нове** (AC-028) |
| **Відправлено (`sent_on`), Відправив (`sent_by`)** | datetime / m2o `res.users`, readonly | кнопка | **нове** |
| Закупівля дистриб'ютора (`purchase_id`) | m2o `purchase.order`, readonly | «Передати дистриб'ютору» | — |
| Дистриб'ютор (`distributor_id`) | related `purchase_id.partner_id` | — | — |
| Дата повернення (`return_date`) | date compute | `date_planned` рядка закупівлі | змінює закупівельник у Закупівлях |
| Проблеми за заміром (`td_measure_problems`) | text compute | замір-листи замовлень МО | хвиля 2, F-62 |

**`td.mebli.cutting.sheet`** (аркуш: `product_id`, `lot_id` — лист/обрізок, розміри, `placement_ids`, `offcut_ids`, площі, відхід), **`td.mebli.cutting.placement`** (деталь на аркуші: `part_id`, `production_id`, позиція, розміри, `rotated`), **`td.mebli.cutting.offcut`** (обрізок результату: розміри, площа, `lot_id`) — зріз, без змін; заповнюються імпортом результату програми розкрою (формат — CSV за шаблоном, як імпорт специфікації) або вручну.

## 2. Кнопки-дії

| Кнопка | Коли видно | Що робить | Після |
|---|---|---|---|
| Передати на розкрій | `state == 'draft'` | перевірка за заміром (§3) → CSV деталей у вкладення, `bom_version`, `sent_on`, деталі `locked` | стан «відправлено»; чат |
| Передати дистриб'ютору | `state == 'draft'` | перевірка за заміром → закупівля товару-послуги `td_material_kind = 'cutting'` у постачальника з `product.supplierinfo` (строк `delay`), файл деталей — вкладенням закупівлі | стан «відправлено»; прогноз замовлення з причиною «Порізка в дистриб'ютора» (AC-026); без постачальника — UserError AC-027 |
| Імпортувати результат | `state == 'sent'` | CSV карти розкрою → аркуші, розміщення, обрізки; деталь не з завдання — UserError «Деталь <код> не належить завданню» | стан «результат» (AC-131) |
| Прийняти обрізки (B) | `state == 'result'` і `group_feature_offcut` | обрізки ≥ мін. розміру → `stock.lot` з `td_is_offcut`, розмірами, `td_cutting_job_id`; оприбуткування стандартним коригуванням залишку | стан «закрито» (AC-059) |
| Підібрати обрізок (B) | на деталі | список `stock.lot` `td_is_offcut`, той самий `product_id`, вільні, розміри ≥ деталі з поворотом | резерв під завдання (AC-060) |

## 3. Перевірка за заміром перед розкроєм (F-62) — хвиля 2
Майстер `td.mebli.measure.warning` (TransientModel): `job_ids`, `method` (яку дію продовжити), `problems` (text). Правила без AI: виступ техніки за нішу; ширина/глибина виробу рядка більша за нішу, в якій він стоїть; найдовша деталь довша за найбільшу стіну/нішу заміру. Кнопки «Назад, виправити проєкт» (закриває) і «Все одно відправити» (продовжує дію, запис у чаті: користувач і перелік). Заміру немає → повідомлення-попередження в чаті й на формі, дія не блокується (AC-055, AC-056).

## 4. Розширення стандартних моделей
- `mrp.production.td_cutting_job_ids` (many2many), `td_cutting_job_count` (compute) — смарт-кнопка; дія «Створити завдання розкрою» з кількох МО (B — більше одного).
- `stock.lot.td_length_mm`, `td_width_mm` (integer, `aggregator=None`), `td_is_offcut` (boolean, index), `td_cutting_job_id` (m2o), `td_area_m2`, `td_reserved_m2`, `td_reserved_for` (compute) — AI-A08-02.
- `product.template.td_material_kind` + `cutting` «Послуга порізки» (`selection_add`).
- `sale.order.td_delay_reason` + `cutting` (`selection_add`).

## 5. Права
`security.md`: технолог — повні; майстер цеху й комірник — читання й запис; продаж — читання; multi-company.
