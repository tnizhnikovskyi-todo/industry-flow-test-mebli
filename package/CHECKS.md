# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 1, 2026-11-13)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint` і CI C-03 у сесії недоступні; рішення AI, записи 48, 51; `observations/2026-11-13-a14-gates-substitutes.md`). Вердикт замінника не дає APPROVE кроку. Повні звіти гейтів — у звіті `tests/reports/A-14.md`.

## Ревізія package/ (commit SHA)
`SHA: 671b39c108957331bbdf2f2a7c954a90580d0055`

## Прогін C-03
`SHA прогону: 671b39c108957331bbdf2f2a7c954a90580d0055` · статус: `success` (замінник: локальний прогін на чистих базах, не GitHub Actions) · A 282/0 failed, light 268/0, B 287/0, демо (td_mebli_demo) 5/0; тур конфігуратора SKIP (немає websocket-client).

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 671b39c108957331bbdf2f2a7c954a90580d0055 | 671b39c108957331bbdf2f2a7c954a90580d0055 success (локально) | правки | замінники гейтів |
| ee | 671b39c108957331bbdf2f2a7c954a90580d0055 | не запущено | WARN: EE не перевірено | EE недоступна: немає `ODOO_EE_ADDONS_PATH`/EE-бази (ВП-4) |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (агент-рецензент, 44 AC) | правки (3 major, 9 minor) | WARN: EE не перевірено | |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник; 5 minor) | WARN: EE не перевірено | VP 20/20, read-back 23/23 A і light |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | правки (3 major, 4 minor) | WARN: EE не перевірено | |
| odoo19-lint | замінник `boost:odoo19-lint` (ruff з ruff.toml Odoo, flake8, pylint-odoo 10.0.12, grep-правила Odoo 19) | правки (3 minor) | WARN: EE не перевірено | pylint 9.71/10 |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` (одна база: 43 модулі + конфіг + 26 кроків майстер-даних + `-u`) | правки (1 major, 3 minor) | WARN: EE не перевірено | запущено до APPROVE pr-review — режим A-14 (усі правки одним циклом) |

## Правки
| № | опис | код кроку повернення (A-11 / A-12 / A-13) | джерело | редакція |
|---|---|---|---|---|
| 1 | major: «Оновити ціни за курсом» затирає ручні ціни/знижки й дату пропозиції (td_mebli_ua/models/sale_order.py:15-22) | A-11 | pr-review M1 | ce |
| 2 | major: 7 mail.template без noupdate — оновлення затре тексти B-04 (td_mebli_notify, td_mebli_sale data) | A-11 | pr-review M2 | ce |
| 3 | major: «Ціна за історією» усереднює різні валюти й одиниці (td_mebli_purchase/models/purchase.py:34-43) | A-11 | pr-review M3 | ce |
| 4 | major: PIN кіоску відкритим текстом у td.mebli.kiosk, читається всіма користувачами Виробництва (td_mebli_shop/wizard/kiosk.py) | A-11 | security 1 | ce |
| 5 | major: action_td_confirm нарахування без серверної перевірки групи (td_mebli_install/models/accrual.py:118) | A-11 | security 2 | ce |
| 6 | major: cutting.sheet/.placement/.offcut без правила компанії (AC-036) | A-11 | security 3, pr-review m2 | ce |
| 7 | major: шаблони атрибутів без td_component_role / значень без td_component_product_id, td_edge_thickness — «Шафа-купе» не підтверджується | A-13 | track-convergence 1 | ce |
| 8 | minor: td_over_history не залежить від VP-11 | A-11 | pr-review m1 | ce |
| 9 | minor: action_td_reset звірки міграції без перевірки групи | A-11 | pr-review m3, security 6 | ce |
| 10 | minor: cron/послідовність BAS без noupdate | A-11 | pr-review m4 | ce |
| 11 | minor: параметр поза діапазоном зриває установку td_mebli_base (hooks.py) | A-11 | pr-review m5 | ce |
| 12 | minor: AC-098 тексти помилок акта не за SPEC | A-11 | pr-review m6 | ce |
| 13 | minor: мости fsm і planning обидва перезаписують групи одного меню | A-11 | pr-review m7 | ee |
| 14 | minor: AC-131 імпорт результату розкрою шукає лот без компанії/товару | A-11 | pr-review m8 | ce |
| 15 | minor: t-esc → t-out (workorder_sheet_report.xml:34) | A-11 | pr-review m9 | ce |
| 16 | minor: CSV деталей розкрою без csv_safe | A-11 | security 4 | ce |
| 17 | minor: публічний td_update_nbu_rates | A-11 | security 5 | ce |
| 18 | minor: time.sleep у кіоску, порівняння PIN не константне | A-11 | security 7 | ce |
| 19 | minor: raise в unlink() → @api.ondelete (td_mebli_bas/models/accrual.py:20) | A-11 | lint L-1 | ce |
| 20 | minor: 59 sudo() без коментаря | A-11 | lint L-2 | ce |
| 21 | minor: Access Rights Inconsistency у order_cost_report_views.xml | A-11 | lint L-3 | ce |
| 22 | minor: умови оплати пакета без td_milestone → контроль доплати 100 % замість 90 % | A-11 | config 1, convergence 2 | ce |
| 23 | minor: обмеження SPEC §11.3 для light (VP-04, кіоск, VP-14/15) не перевіряються | A-12 | config 2, 3 | ce |
| 24 | minor: VP-16 default: схема true ↔ модуль False; 14 тестів крихкі до значення | A-11 | config 4, convergence 4 | ce |
| 25 | minor: 4 тести шукають англійські рядки на uk_UA | A-11 | convergence 4 | ce |
| 26 | minor: застарілий текст CONFIG.md (AC-107), install-log light | A-12 | config 5 | ce |
| 27 | minor: route_ids Buy/Manufacture мовчки відкидаються в шаблонах товарів | A-13 | convergence 3 | ce |

## Зведений вердикт
`правки` — повернення: A-11 (№1–6, 8–22, 24, 25), A-12 (№23, 26), A-13 (№7, 27). EE — `WARN: EE не перевірено`. Цикл A-11/12/13 → A-14: 1.
