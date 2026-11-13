# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 2, 2026-11-13)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint` і CI C-03 у сесії недоступні; рішення AI, записи 48, 51; `observations/2026-11-13-a14-gates-substitutes.md`). Вердикт замінника не дає APPROVE кроку. Повні звіти гейтів — у звіті `tests/reports/A-14.md`.

## Ревізія package/ (commit SHA)
`SHA: 935b591efcdc91badf2dc4f80cd16a3dbb84987d`

## Прогін C-03
`SHA прогону: 935b591efcdc91badf2dc4f80cd16a3dbb84987d` · статус: `success` (замінник: локальний прогін на чистих базах, не GitHub Actions) · A 301/0 failed, light 285/0, B 306/0, A uk_UA 301/0, демо 5/0; налаштована база (модулі+конфіг+майстер-дані) A 301/0; тур конфігуратора SKIP (немає websocket-client).

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 935b591efcdc91badf2dc4f80cd16a3dbb84987d | 935b591efcdc91badf2dc4f80cd16a3dbb84987d success (локально) | правки | замінники гейтів |
| ee | 935b591efcdc91badf2dc4f80cd16a3dbb84987d | не запущено | WARN: EE не перевірено | EE недоступна: немає `ODOO_EE_ADDONS_PATH`/EE-бази (ВП-4) |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` | APPROVE (замінник; 1 minor) | WARN: EE не перевірено | 26/27 правок циклу 1 закрито, №9 частково |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник; 2 minor) | WARN: EE не перевірено | preflight PF-01…09 = SPEC §11.3 |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник; 2 minor) | WARN: EE не перевірено | |
| odoo19-lint | замінник `boost:odoo19-lint` | правки (1 minor) | WARN: EE не перевірено | L-2, L-3 закрито; L-1 частково |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | правки (1 major) | WARN: EE не перевірено | «Шафа-купе» SO→MO для 3 декорів; 28/28 кроків даних; тести на налаштованій базі 301/0 |

## Правки
Цикл 1 (спроба 1, SHA 671b39c): 27 правок — 26 закрито, №9 частково (див. tests/reports/A-14.md). Відкриті після спроби 2:
| № | опис | код кроку повернення (A-11 / A-12 / A-13) | джерело | редакція |
|---|---|---|---|---|
| 28 | major: специфікація замовлення рахує плиту й кромку двічі — рядки з деталей + статичні рядки шаблону (DSP-18-W, EDGE-W; `td_mebli_mrp/models/mrp_bom.py:194-198`, `master-data/11_mrp.bom.line.csv`); для дуба/графіту МО вимагає білу плиту (AC-013) | A-11, A-13 | track-convergence TC2-1 | ce |
| 29 | minor (№9 залишок): фінансист через RPC змінює explanation/state звірки або створює її «поясненою» без підпису менеджера | A-11 | security S-N1 | ce |
| 30 | minor: бухгалтер повертає підтверджене нарахування в чернетку, змінює суму, скасовує без причини | A-11 | security S-N2 | ce |
| 31 | minor (L-1 залишок): `raise` в `unlink()` — `td_mebli_install/models/accrual.py:119-122` → `@api.ondelete` | A-11 | lint | ce |
| 32 | minor: текст ризику R3-X-01 («за датою пропозиції») ≠ реалізація (правило прайсу на сьогодні) | A-11 | pr-review P-N1 | ce |
| 33 | minor: CONFIG.md:115 послідовність кроку 22 → 24 | A-12 | config C-N1 | ce |
| 34 | minor: повторне застосування з VP-05=false лишає ir.default на архівну умову оплати | A-12 | config C-N2 | ce |

## Зведений вердикт
`правки` — повернення: A-11 (№28–32), A-12 (№33, 34), A-13 (№28). EE — `WARN: EE не перевірено`. Цикл A-11/12/13 → A-14: 2.
