# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 8, 2026-11-16)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка`. Причина — рішення власника 2026-11-16 (`flow/decisions.md` рядок 53): обмін з BAS/BAF відкладено зі збірки — A-11-fix5 (`td_mebli_bas`, `td_mebli_attendance`, `convert_bas.py` → `package/deferred/`; `td_mebli_demo`, `_migration`, `_install`, `_ua`, `_cutting`, `_sale` — без BAS; `td_mebli_mrp` — права технолога, рішення власника 2026-11-16, D-23), A-12-6 (модулі до установки, VP-04 = false, PF-10), A-13-5 (шаблони `td/19b`–`21b` відкладено, 25 кроків імпорту). Обсяг: `git diff f48d954..e682ecb -- package/`.

## Ревізія package/ (commit SHA)
`SHA: e682ecb09c286f8fd5b8342e50998c18a73f399f`

## Прогін C-03
`SHA прогону: e682ecb` · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). `tools/odoo/` на чистих базах, Odoo 19.0 CE, uk_UA, окремий каталог доставки `/home/user/odoo19/delivery-bas` (без відкладених модулів): `clean_db` → `install.sh` (модулі `apply.py plan` профілю) → `run_tests.sh`.

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 45 модулів) | test-mebli-bas-a148-A | 328 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| light (`profiles/answers.alt-1.yaml`, 45) | test-mebli-bas-a148-light | 328 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| B (`profiles/answers.alt-2.yaml`, 46) | test-mebli-bas-a148-B | 333 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |

Формат клітинки — тестів / failed+error. Проти спроби 7 (349/333/354): мінус тести відкладених `td_mebli_bas` (14), `td_mebli_attendance` (7) і конвертора BAS (1); новий `test_ac_089_no_steps_of_deferred_modules` замість `test_ac_089_bas_steps_need_td_mebli_bas`; новий `test_d23_technologist_prepares_products_and_specifications` (рішення власника 2026-11-16 (права технолога), D-23). `td_mebli_bas`/`td_mebli_attendance` у жодній базі — немає (`hr_attendance` — installed). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | e682ecb09c286f8fd5b8342e50998c18a73f399f | e682ecb success (локально) | APPROVE (замінники) | правок немає |
| ee | e682ecb09c286f8fd5b8342e50998c18a73f399f | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); змінені модулі EE-частини не мають, `depends` без EE/AGPL |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff f48d954..e682ecb) | APPROVE (замінник) | WARN: EE не перевірено | залежностей на відкладені модулі 0 (grep `depends`, моделей `td.mebli.bas.*`, полів `td_bas_*`, `convert_bas`); `td_mebli_demo` → `hr_attendance`; міграція `td_mebli_migration` 19.0.1.1.7 прибирає кроки 26–28 (`noupdate`); знахідок 0; info N8-1, N8-2 |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | нові ACL лише групи «Технолог» (D-23, рішення власника 2026-11-16): read/write/create без unlink на 9 моделях + `resource.resource` (AI-39), правил записів не додано; маршрутів не додано; прибрано 3 правила й ACL відкладених моделей разом з модулем; `sudo` у `_td_cancel_pay_marks` — без змін (лише коментар) |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | «Модулі до установки» ce/ee без `td_mebli_bas`, `td_mebli_attendance`; VP-04 = false у схемі й усіх профілях; PF-10 зупиняє `true` (негативний тест `apply.py plan`) |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | ruff змінених .py — нових знахідок 0 (test_migration 18 → 15; full.py — давні); `.pot`/uk.po — прибрані записи відповідають коду (test_d13/test_d16 `td_mebli_base` — PASS) |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-mebli-bas-a148-cv`: модулі 45 + конфіг (8/4/14; повтор unchanged 26) + майстер-дані 25/25 (91 запис) + compare diff 0 + read-back 23/0 + smoke OK; кроків імпорту в базі 25 |

## Покриття ALLOCATION
- `package/addons/`: обсяг diff — 7 змінених модулів (`td_mebli_demo`, `_migration`, `_install`, `_ua`, `_cutting`, `_sale`, `_mrp`) і 2 перенесені в `package/deferred/` (AC-039…AC-042, AC-078, AC-109 — «відкладено рішенням власника 2026-11-16», не «не пройдено»); C-03 — усі встановлені `td_*` профілів A/light/B (мости EE — не перевірено).
- `package/config/`, `package/master-data/`: змінено (A-12-6, A-13-5); track-convergence на налаштованій базі A.
- Покриття 100 % (CE) для AC збірки; відкладені AC поза обсягом до окремого рішення власника.

## Правки
Цикли спроб 1–7: №1–40, D-18…D-21, UI-1, UI-2, T-1 закрито. У спробі 8 нових правок немає.

Info — не правки, без коду повернення:
- **N8-1.** Профілі light і A тепер однакові за модулями (різниця — лише параметри SPEC §11.3) — наслідок рішення власника (AI-37).
- **N8-2.** Оновлення бази, де `td_mebli_bas`/`td_mebli_attendance` уже стоять, не перевірено (бази клієнта немає): порядок «спершу видалити модулі» — AI-38, `package/deferred/README.md`, `admin.md` § «Обмін з обліковою системою».

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — спроба 8 на `e682ecb`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Правок немає; обмін з BAS/BAF відкладено рішенням власника 2026-11-16 (`flow/decisions.md` рядок 53).
- C-03 — success: локальний прогін на `e682ecb` (A 367, light 367, B 372 тестів; 0 failed).
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
