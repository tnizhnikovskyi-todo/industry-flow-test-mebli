# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 6, 2026-11-15)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка`. Причина — контур коду 2: A-16b (аудит прав ролей) повернув D-18…D-21 (`package/demo/defects.md`), виправлено в A-11-fix3 (`ba0aff3`, `tests/reports/A-11-fix3.md`). Обсяг: `git diff ae1763e..ba0aff3 -- package/` — 33 файли модулів `td_mebli_install`, `td_mebli_mrp`, `td_mebli_claim`, `td_mebli_demo` (+ AI-DECISIONS AI-25…AI-28). `package/config`, `package/master-data` не змінювались. Попередня спроба (5, `795f6b1`, APPROVE (CE)) — `tests/reports/A-14-5.md`; повні звіти гейтів спроби 6 — `tests/reports/A-14-6.md`.

## Ревізія package/ (commit SHA)
`SHA: ba0aff368db22e55bb3af73f8d07d09ffdc31b5e`

## Прогін C-03
`SHA прогону: ba0aff3` · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). `tools/odoo/` на чистих базах, Odoo 19.0 CE, uk_UA: `clean_db.sh` → `install.sh <модулі apply.py plan> --addons-src package/addons --lang uk_UA` → `run_tests.sh` (td_mebli_* — одним прогоном з турами; `td_knowledge`+`td_mebli_knowledge`, `td_support`, `td_home_menu` — окремо). Демо-шар: база B + `td_mebli_demo`, `/td_mebli_demo` (A-11-fix3).

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 47 модулів) | test-mebli-fix3-a146-c1-A | 347 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |
| light (`profiles/answers.alt-1.yaml`) | test-mebli-fix3-a146-c1-light | 331 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |
| B (`profiles/answers.alt-2.yaml`) | test-mebli-fix3-a146-c1-B | 352 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |
| B + `td_mebli_demo` | test-mebli-fix3-b | /td_mebli_demo 16 / 0 | — | — | — |

Формат клітинки — тестів / failed+error. Нові тести A-11-fix3: +14 у td_mebli_* (D-19 6, i18n 1, D-20 4, D-21 3), +4 у td_mebli_demo (D-18). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | ba0aff368db22e55bb3af73f8d07d09ffdc31b5e | ba0aff3 success (локально) | APPROVE (замінники) | правок немає |
| ee | ba0aff368db22e55bb3af73f8d07d09ffdc31b5e | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); змінені модулі EE-частини не мають, `depends` без EE/AGPL |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff ae1763e..ba0aff3) | APPROVE (замінник) | WARN: EE не перевірено | D-18…D-21 закрито за SPEC з рішеннями AI-25…AI-28; знахідок 0; info N6-1…N6-3 |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | нові права: запис `project.task` менеджером — ACL + `ir.rule` (свої замовлення) + перелік полів у `write`; `sudo` у D-21 — після `check_access('write')` на рекламацію, з коментарем; група технолога — RWCD лише `td.mebli.*` моделей SPEC §2; публічних маршрутів немає |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | `package/config` не змінено; «Модулі до установки» ті самі (версії модулів — патч) |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | pylint-odoo (odoolint, E, F) 4 змінених модулів — нових знахідок 0 (E0401 — середовище lint без Odoo; E0203 `payment.py:115` — давнє, не з diff); ruff нових/змінених py — 0; uk.po — `test_i18n_po` PASS |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-mebli-fix3-a146-c1-cv`: модулі 47 + конфіг (8/4/14) + майстер-дані 28/28 (97 записів) + compare diff 0 + read-back 23/23 + smoke OK; статей бази знань 8 |

## Покриття ALLOCATION
- `package/addons/`: обсяг diff — 4 модулі (`td_mebli_install`, `_mrp`, `_claim`, `_demo`); C-03 — усі встановлені `td_*` профілів A/light/B (мости EE — не перевірено).
- `package/config/`, `package/master-data/`: без змін; track-convergence на налаштованій базі A.
- Покриття 100 % (CE).

## Правки
Цикли спроб 1–5: №1–40 закрито (F-38…F-40 — `795f6b1`). У спробі 6 нових правок немає.

Закрито до гейтів (A-11-fix3, `ba0aff3`; джерело — A-16b, `package/demo/defects.md`):
| № | файл | опис | серйозність | статус |
|---|---|---|---|---|
| D-19 | td_mebli_install: views/act_views.xml, security/*, models/act.py | менеджер салону відкриває «Календар монтажів» (Продажі) і змінює дату/бригаду виїздів своїх замовлень | середній | закрито (ba0aff3) |
| D-20 | td_mebli_mrp: security/td_mebli_mrp_groups.xml, ir.model.access.csv, меню | група «Технолог»: RWCD правила деталей, деталі, шаблони імпорту; меню «Виробництво → Налаштування» | середній | закрито (ba0aff3) |
| D-21 | td_mebli_claim: models/repair.py, views/repair_views.xml | сервіс створює пропозицію платного ремонту; store кнопки не бачить | високий | закрито (ba0aff3) |
| D-18 | td_mebli_demo: hooks.py, data/workcenter_data.xml | демо-шар переймає дільниці A-13 — без дублів (перевірка стенда — A-15-full-2) | низький | закрито (ba0aff3) |

Info — не правки, без коду повернення:
- **N5-1, N5-2** — як у спробі 5 (без `company_id` у `td.support.request`, `td.knowledge.article`; `td_reader_tree` `search([])`).
- **N6-1.** Користувач з `project.group_project_user` і групою продавця отримує ще й запис виїздів своїх замовлень у проєктах «лише підписникам» (правила груп поєднуються через «або») — свідомо (AI-25).
- **N6-2.** Технолог бачить у «Налаштуванні» виробництва ще «Робочі центри» й «Операції» (лише читання, якщо ввімкнено маршрути); `mrp.group_mrp_user` зберігає RWCD на шаблони імпорту (SPEC §2: майстер «—») — AI-26.
- **N6-3.** xmlid `td_mebli_mrp.group_technologist` ≠ `td_mebli_base.group_technologist` у `tr/security.md` §1 — оновити SPEC (A-08), AI-26.

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — спроба 6 на `ba0aff3`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Правок немає; дефекти A-16b D-18…D-21 закрито в A-11-fix3.
- C-03 — success: локальний прогін на `ba0aff3` (A 383, light 367, B 388 тестів; 0 failed) + `/td_mebli_demo` 16 / 0.
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
