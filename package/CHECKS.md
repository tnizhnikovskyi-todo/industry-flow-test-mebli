# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 4, 2026-11-14)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint` і CI C-03 у сесії недоступні; рішення AI, записи 48, 51; `observations/2026-11-13-a14-gates-substitutes.md`), режим «перевірка після змін» (`params.mode: перевірка`). Причина — повернення з A-17 (спроба 1): `package/` змінено після гейтів `1925fb8` (A-11-6 демо-податки, A-11-7 дефекти стенда D-02…D-15, A-11-8 `.pot`/`report.url`, A-12-5 D-10). Обсяг: `git diff 1925fb8..21afe46 -- package/addons package/config package/master-data` (110 файлів). Повні звіти гейтів — `tests/reports/A-14-4.md`.

## Ревізія package/ (commit SHA)
`SHA: 21afe461b593b35f6fc06c5e7c63213be7f4d2b0`

## Прогін C-03
`SHA прогону: 16a74c6` · статус: `success` (замінник: локальні прогони, повторно не запускались). Код `package/` на `21afe46` той самий: `git diff 16a74c6..21afe46 -- package/` змінює лише `package/ACCEPTANCE.md`.
- A-11-8: профіль A — 332 тести, 0 failed (з турами); демо — 12, 0 failed.
- A-11-7: A — 330/0, light — 314/0, B — 335/0.
- A-15-5: стенд з гілки `16a74c6` — OK. A-16-3: FAIL 0.
- Остаточний код `239b051` (≡ `21afe46` ≡ `16a74c6` за `package/addons`, `config`, `master-data`), чисті бази `test-pkg-mebli-r5-*`, тести всіх td_mebli_* профілю з турами (2026-11-14): light — 316 тестів, 0 failed / 0 error, skipped 1; B — 337, 0 / 0, skipped 1. Застереження A-14-4 «light/B лише на коді A-11-7» закрито (`tests/reports/A-14-4.md` «Застереження»).

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 21afe461b593b35f6fc06c5e7c63213be7f4d2b0 | 16a74c6 success (локально; код ідентичний 21afe46) | APPROVE (замінники) | 0 правок |
| ee | 21afe461b593b35f6fc06c5e7c63213be7f4d2b0 | не запущено | WARN: EE не перевірено | EE недоступна: немає `ODOO_EE_ADDONS_PATH`/EE-бази (ВП-4); мости EE без `.pot` (на CE не встановлюються) |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 1925fb8..21afe46) | APPROVE (замінник) | WARN: EE не перевірено | 0 major, 0 minor. Без знахідок: D-02 inverse стадії, D-04 inverse розмірів, вкладки D-05/D-12, кнопка D-11, демо-податки D-01 |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | A-12-5: конфіг без змін (D-10 — дані виробу, демо `hooks.py`). Меню D-07: `groups="-…feature_nbu,…group_finance"` (odoo/tools/convert.py:320) |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | Нова група «Сервіс» відповідає tr/security.md:15; замірник має лише `group_td_mebli_measurer`. `sudo` у D-06/D-08 — лише після `check_access('write')`. 2 info: N4-1, N4-2 |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | pylint-odoo: 9.74/10 (було 9.73), E-кодів 0, нові — 2 × W8150 у тестах. ruff: +9/−1, усе стиль (7 у тестах). uk.po: 24 з 24 розбираються, неперекладених 0, плейсхолдери збігаються |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | Вердикт перенесено: `package/addons` після 16a74c6 не змінювався. A-16-3: AC-015, 017, 019 — PASS. Конфіг ідемпотентний (A-12-5: 2-й прохід, diff 0) |

## Правки
Цикли 1–3 (671b39c, 935b591, a5a1063): №1–37 закрито (№35–37 — A-11-5, `1925fb8`). Спроба 4 (21afe46): **нових правок немає**.

Info — не правки, без коду повернення:
- **N4-1.** ACL `product.supplierinfo` (td_mebli_purchase/security/ir.model.access.csv:4) дає `purchase.group_purchase_user` права RWC. Це ширше за стандарт Odoo 19, де так можуть лише purchase/product manager. Закупівельник змінює ціни постачальника будь-якого товару, і не лише через імпорт прайсу. Це рішення D-06 (AC-087), воно описане в `package/demo/defects.md`. У tr/security.md рядка про нього немає — додати під час наступної правки ТР.
- **N4-2.** Демо-функція `_bas_codes` (td_mebli_demo/full.py:573-592) нумерує коди від кількості вже заданих. Якщо в нумерації є пропуски, коди можуть повторитися. Унікального обмеження немає, тож падіння не буде. Стосується лише демо.

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — замінники за рішенням власника, запис 52 (`flow/decisions.md`, варіант (а)).
- Правок 0. Усі п'ять гейтів-замінників на `21afe46` — APPROVE.
- C-03 — success: локальні прогони на ідентичному коді `16a74c6`.
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» ухвалює людина на A-17/A-18. Рядок у flow/decisions.md вносить людина.
