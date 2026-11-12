# `td_mebli_measure` — замір-лист і запис на замір

**Призначення.** S-15 (F-19, F-20, F-48, F-54); перевірка за заміром перед розкроєм (F-62) спирається на ці дані. Коробка A. AC: AC-001…AC-010, AC-055.
**Звірка:** `addons/crm/models/crm_lead.py:85`; `addons/sale_crm/models/sale_order.py:10` (`opportunity_id`); `addons/calendar/models/calendar_event.py:71`; `addons/calendar/models/calendar_alarm.py:8`; `addons/web/static/src/core/ui/ui_service.js:154` (`isSmall` — мобільний режим). PLAN.md «Модель даних»: `td.mebli.measure`, `.niche`, `.appliance`.

## 1. Замір-лист (`td.mebli.measure`, `_inherit = ['mail.thread']`) — зріз

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Номер (`name`) | char, readonly | `ir.sequence` `td.mebli.measure` (префікс `ЗМ/%(year)s/`) | required |
| Нагода (`lead_id`) | many2one `crm.lead` | контекст / `order_id.opportunity_id` | tracking |
| Замовлення (`order_id`) | many2one `sale.order` | контекст | tracking |
| Компанія (`company_id`) | many2one `res.company` | замовлення / нагода | required, правило multi-company |
| Покупець (`customer`) | char compute | партнер нагоди/замовлення | — |
| Замірник (`measurer_id`) | many2one `res.users` | поточний користувач | domain: група `group_measurer` |
| Приміщення (`room`), Нахил підлоги, мм (`floor_slope_mm`), Кут стін, ° (`wall_angle_deg`), Комунікації (`utilities`) | char / integer / float / text | замірник | — |
| Ніші (`niche_ids`), Техніка (`appliance_ids`) | one2many | замірник | — |
| Фото (`photo_ids`) | many2many `ir.attachment` | камера / галерея | — |
| Стан (`state`) | selection: «Виміряно» / «Звірено з проєктом» | кнопка «Звірити з проєктом» | — |
| Не вміщається (`issue_count`), Що не вміщається (`issue_text`) | integer / text compute | ніші й техніка | AC-008 |

**`td.mebli.measure.niche`:** `measure_id` (m2o, cascade), `name` (required), `width_mm`, `height_mm`, `depth_mm`, `protrusion_mm` (integer), `order_line_id` (m2o `sale.order.line` — виріб у ніші; розмір модуля — з `td_width/td_depth` рядка, AC-009).
**`td.mebli.measure.appliance`:** `measure_id`, `name`, `niche_id` (domain — ніші цього листа), `width_mm`, `height_mm`, `depth_mm`, `fits` (boolean compute), `issue` (char compute). Правило `fits`: якщо будь-який розмір техніки або ніші порожній → `issue` = «Не перевірено (немає розмірів)», `fits` = True, у лічильник не йде (AC-010); інакше техніка ≤ ніша + виступ і (за наявності) техніка ≤ модуль ≤ ніша; повідомлення «Не вміщається: глибше на N мм».

**Розширення:** `sale.order.td_measure_ids` (o2m), `td_measure_count`, `td_measure_problems` (text compute); `crm.lead.td_measure_ids`; `mrp.production.td_measure_problems` (банер на МО).

## 2. Запис на замір (F-54) — хвиля 2
Майстер `td.mebli.measure.booking` (TransientModel): `lead_id` (required), `partner_id` (related), `measurer_id` (m2o `res.users`, required, domain групи замірника), `date_from` (date, default сьогодні), `days` (integer, default 5), `slot_ids` (o2m `td.mebli.measure.slot`: `start`, `stop`, `day`, `label`). Вікна — робочі інтервали календаря роботи компанії мінус `calendar.event` замірника (`partner_ids` містить партнера замірника). Порожній список → UserError «Немає вільних вікон за обраний період — збільште кількість днів або оберіть іншого замірника» (AC-003). Вибір вікна створює `calendar.event` (`opportunity_id`, учасники — замірник і покупець, тип «Замір», нагадування — `calendar.alarm` з конфіг-пакета, AC-004).

## 3. Права
`security.md` §2–§3: свої заміри (замірник), заміри своїх замовлень (продаж), усі (старший продаж, цех, керівник); multi-company. Замірник не має доступу до `sale.order` на читання цін: форма заміру показує адресу й телефон покупця через compute з `sudo()` лише цих двох полів (лише читання).

## 4. UI/UX
Меню «CRM → Заміри» і «Заміри → Мій календар» (подання `calendar` подій замірника). Форма заміру: шапка — номер, покупець, адреса, телефон (`widget="phone"`), стан, лічильник «Не вміщається» (червоний); вкладки «Ніші», «Техніка», «Фото» (`widget="many2many_binary"`), «Приміщення». Кнопки: «Звірити з проєктом» (`invisible="not order_id"`), «Записати на замір» (на нагоді). На телефоні (`isSmall`) ніші й техніка — `<kanban>` картками.
