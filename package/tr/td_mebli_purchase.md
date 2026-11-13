# `td_mebli_purchase` — ціна проти історії, імпорт прайсу постачальника

**Призначення.** S-08 (F-35, F-59; F-12 — стандарт). Коробка A. AC: AC-084…AC-087.
**Звірка:** `addons/purchase/models/purchase_order_line.py:46` (`price_unit`); `addons/purchase/report/purchase_report.py:14` (аналіз закупівель — F-12 стандарт); `addons/product/models/product_supplierinfo.py:13` (`partner_id`), `:20` (`product_code`), `:27` (`min_qty`), `:30` (`price`), `:40` (`date_start`), `:51` (`delay`); читання xlsx — як у `addons/base_import/models/base_import.py:481` (`openpyxl`).

## 1. Розширення `purchase.order.line` — зріз

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Ціна за історією (`td_history_price`) | monetary compute, store | середня `price_unit` підтверджених рядків того самого товару за 180 днів, у валюті рядка | store — для фільтра; перерахунок при зміні товару/ціни |
| Проти історії, % (`td_price_delta_pct`) | float compute, store | (ціна − історія) / історія | без історії — 0 і порожня історія (AC-086) |
| Переплата (`td_overpay`) | monetary compute, store | (ціна − історія) × кількість | — |
| Вище історії (`td_over_history`) | boolean compute, store | `td_price_delta_pct > company.td_price_threshold_pct` | у зрізі поріг — у коді (R-04); фільтр і показник дашборда (AC-085) |

## 2. Майстер імпорту прайсу (`td.mebli.price.import`, TransientModel) — хвиля 2
Поля: `partner_id` (постачальник, required), `file`/`filename` (xlsx/csv, required), `date_start` (дата дії, default сьогодні), `mapping` (розпізнані колонки), `line_ids` (o2m `td.mebli.price.import.line`), лічильники `unknown_count`, `change_count`. Рядок: `code`, `name`, `product_id` (за кодом постачальника `product_code` або внутрішнім кодом), `price`, `old_price`, `min_qty`, `delay`, `supplierinfo_id`, `status` (`new` «Нова ціна» / `update` «Ціна змінилась» / `unchanged` / `unknown` «Код не знайдено»).
**Правила:** «Записати» створює або оновлює `product.supplierinfo` (постачальник, товар, ціна, `min_qty`, `delay`, `date_start`) лише для `new`/`update`; `unknown` не пишуться й лишаються у звіті (AC-087). Нові ціни отримують сигнал історії вже в закупівлях.

## 3. Права й UI
Закупівельник — повні; керівник, фінансист — читання (`security.md`). Меню «Закупівлі → Імпорт прайсу», фільтр «Вище історії» у рядках закупівель, колонки «Ціна за історією», «Проти історії, %».
