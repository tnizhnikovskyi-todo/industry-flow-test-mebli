# `td_mebli_base` — групи, параметри компанії, спільні ресурси (новий)

**Призначення.** Спільна основа всіх `td_mebli_*`: групи ролей і feature-групи коробок (`security.md`), параметри анкети `answers.yaml` на рівні юрособи (AI-A08-04), налаштування в «Налаштування → Меблі», шрифт PDF з кирилицею (AI-A08-20). Коробка A. AC: AC-018, AC-020, AC-033, AC-034, AC-036, AC-067, AC-085, AC-104, AC-111, AC-N.06, AC-N.07.

## 1. Поля `res.company` (параметри анкети)

Нові поля на `res.company` (`odoo/addons/base/models/res_company.py:32`), показ — `res.config.settings` полями `related='company_id.<поле>', readonly=False` (стандартний патерн налаштувань компанії, `odoo/addons/base/models/res_config.py`).

| Назва поля | Тип поля | Звідки значення | Примітка |
|---|---|---|---|
| Режим договору (`td_contract_mode`) | selection: `contract` «Договір підряду» / `sale` «Купівля-продаж» | анкета A-12, `contract_mode` (SPEC §11.2; `unset` → поле порожнє) | без значення — друк договору блокується (AC-034); заміняє `ir.config_parameter` зрізу `td_mebli_sale` |
| Контроль доплати (`td_payment_control`) | selection: `warn` «Попереджати» / `block` «Блокувати»; default `warn` | анкета, VP-06 | заміняє `td_mebli_install.payment_control` (AC-020) |
| Менеджер бачить маржу (`td_margin_to_salesman`) | boolean, default False | анкета, VP-08 | при зміні — додає/знімає `group_margin_view` усім користувачам групи «Продажі: власні документи» компанії (AC-018) |
| % бригаді (`td_crew_pct`) | float (5,2), default 0 | дані клієнта B-04, не VP (AI-A08-24; значення клієнта; вакансії 7,5–20 % — лише довідка) | дефолт `crew_pct` нового акта (AC-104) |
| Поділ між бригадою (`td_crew_split`) | selection: `equal` «Порівну» / `time` «За часом» | анкета, VP-14 | AC-104 |
| База % бригаді (`td_crew_base`) | selection: `final` «За фінальним актом» / `stage` «За етапами» | анкета, VP-15 | AC-103 |
| Монтаж у вартості (`td_install_in_price`) | boolean | анкета, VP-16 (AI-08) | режим рядка-послуги з нульовою ціною (AC-043) |
| Застряглі, днів (`td_stuck_days`) | integer, default 5 | анкета, VP-10 | заміняє константу `STUCK_DAYS` (AC-067) |
| Поріг ціни вище історії, % (`td_price_threshold_pct`) | float, default 5.0 | анкета, VP-11 (ціле %) | AC-085 |
| Мінімальний обрізок, мм (`td_min_offcut_mm`) | integer, default 300 | анкета, VP-12 | дефолт для завдання розкрою (AC-059) |
| Прострочка рекламації, днів (`td_claim_overdue_days`) | integer, default 14 | анкета, VP-13 | AC-110 |
| Нагадування про доплату, днів до виїзду (`td_pay_reminder_days`) | integer, default 2 | анкета, VP-07 | AC-031 |
| Чек-лист акта (`td_act_checklist`) | text (translate) | дані клієнта B-04, не VP (AI-A08-24; типовий 8–12 пунктів) | AI-A08-16 (AC-097) |
| Тексти перевірено юристом (`td_legal_checked`) | boolean, default False | після висновку юриста (№17) | прибирає позначку «Шаблон до перевірки юристом» з договору й актів (AC-033, `print-forms.md`) |
| Профіль коробки (`td_box_profile`) | selection: `light` / `A` / `B` / `C` | конфіг-пакет з VP-01 і `edition` (C = VP-01 `B` + `ee`, AI-A08-21) | лише інформаційне; функції вмикають feature-групи |

## 2. Поле категорії товару

| Назва поля | Тип | Звідки | Примітка |
|---|---|---|---|
| Гарантія, міс. (`product.category.td_warranty_months`) | integer | після юриста (№17), до того порожнє | AI-A08-17, AC-111 (`addons/product/models/product_category.py:9`) |

## 3. Налаштування (UI)
Розділ «Меблі» в `res.config.settings` (форма налаштувань): блоки «Договір і оплата» (режим, контроль доплати, нагадування), «Монтаж» (% бригаді, поділ, база, у вартості, чек-лист), «Контроль» (застряглі, поріг ціни, прострочка рекламації, мінімальний обрізок), «Функції коробки B» (галочки `group_feature_*` через `implied_group`, `odoo/addons/base/models/res_config.py:256`; значення з анкети — VP-02). Видно групі `base.group_system` і `td_mebli_base.group_director` (лише читання для керівника).

## 4. Шрифт PDF
`static/fonts/` — вільний шрифт з кирилицею; `web.report_assets_common` успадковується (`<template inherit_id>`), `@font-face` і `font-family` для `.td_mebli_report`. Звіти пакета мають кореневий клас `td_mebli_report`. Ліцензію шрифту фіксує `README.md` модуля (AI-A08-20, AC-N.06).

## 5. Міграції
`migrations/19.0.1.1.0/post-migrate.py`: перенести `ir.config_parameter` `td_mebli_sale.contract_mode`, `td_mebli_install.payment_control` у поля поточної компанії; користувачів групи зрізу `group_td_mebli_director` — у `group_director` (AC-N.04).
