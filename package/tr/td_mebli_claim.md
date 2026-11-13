# `td_mebli_claim` — рекламація, повторне виготовлення, платний ремонт

**Призначення.** S-14 (F-17, F-18, F-55). Основа — стандартний ремонт `repair.order` (CE, `addons/repair/__manifest__.py`, LGPL-3). Коробка A. AC: AC-080, AC-081, AC-110…AC-112.
**Звірка:** `addons/repair/models/repair.py:42` (`state`), `:63` (`tag_ids`, модель `repair.tags`), `:64` (`under_warranty`), `:67` (`schedule_date`), `:168` (`sale_order_id` — замовлення, з якого продано ремонт; інший зміст), `:447` (`action_create_sale_order`), `:561` (`action_repair_start`), `:571` (`action_validate`). PLAN.md: `repair.order.td_*`, `sale.order.td_claim_*`; рецензія Архітектора, коло 1: причина — стандартні теги, «хто платить» — стандартне `under_warranty`.

## 1. Розширення `repair.order`

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Замовлення меблів (`td_claim_order_id`) | m2o `sale.order` | сервіс | domain — замовлення покупця; `check_company=True` |
| Деталь (`td_part_id`) | m2o `td.mebli.part` | сервіс | domain `[('bom_id.td_sale_order_id', '=', td_claim_order_id)]`; необов'язкова |
| Фото (`td_photo`) | image 1024 | сервіс | решта фото — вкладення чату |
| Повторне виготовлення (`td_remake_production_id`) | m2o `mrp.production`, readonly | кнопка | — |
| Гарантія до (`td_warranty_end`) | date compute, store | дата фінального акта (`td_act_ids`) + `product.category.td_warranty_months` виробу | без строку категорії — порожнє і позначка «Гарантійний строк не задано» (AC-111; AI-A08-17, R-17) |
| Після гарантії (`td_after_warranty`) | boolean compute | — | onchange: `under_warranty = not td_after_warranty`, якщо строк задано |
| Днів відкрито (`td_days_open`), Прострочено (`td_overdue`) | integer / boolean compute | `create_date`; поріг `company.td_claim_overdue_days` | KPI 5; у зрізі — без параметра |

Причини рекламації — стандартні теги `repair.tags` (дані конфіг-пакета: «Виробництво», «Монтаж», «Постачальник», «Транспорт», «Клієнт»). «Хто платить» — стандартне `under_warranty`; відшкодування постачальником — тег «Постачальник» (рішення зрізу).

## 2. Кнопки-дії

| Кнопка | Коли видно | Що робить | Після |
|---|---|---|---|
| Повторне виготовлення | `not td_remake_production_id` | МО на деталь (товар — матеріал/виріб деталі, специфікація з однієї деталі) або на виріб; `origin` = номер рекламації | посилання; без деталі й товару — UserError «Оберіть деталь або виріб для повторного виготовлення» (AC-081) |
| Запланувати виїзд | завжди | задача в проєкті монтажів з посиланням на рекламацію (`repair.order.td_visit_task_id`, m2o `project.task`, readonly — **нове**) і адресою замовлення | календар бригади, денний план (AC-132) |
| Платний ремонт | `td_after_warranty` | стандартна `action_create_sale_order` — пропозиція покупцю | рахунок — стандарт (AC-112) |

## 3. Розширення `sale.order`
`td_claim_ids` (o2m `repair.order` за `td_claim_order_id`), `td_claim_count` (compute, смарт-кнопка «Рекламації»).

## 4. Права й UI
Сервіс — повні (група `group_service` + права `repair`); бригадир — читання й запис; продаж і керівник — читання. Канбан рекламацій за стадіями ремонту з позначкою «Прострочено», фільтри «На гарантії / Після гарантії / Прострочено». На EE з Helpdesk — канбан ховається групою мосту (`ee-bridges.md`).
