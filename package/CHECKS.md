# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 7, 2026-11-15)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка`. Причина — A-11-fix4 (`1778db7`): власні іконки кореневих меню `td_*` у стилі Odoo 19 (`td_knowledge`, `td_mebli_dashboard`, `td_mebli_measure`), головний екран `td_home_menu` у стилі EE власним кодом (навбар — лише systray, білі плитки 88 px, підпис в один рядок з «…» і `title`, 6/4/3 колонки, одна виділена плитка, фон), тести дат `td_mebli_notify` — `freeze_time`. Обсяг: `git diff 0fbcd1d..1778db7 -- package/` — 5 модулів; `package/config`, `package/master-data` не змінювались. Попередня спроба (6, `ba0aff3`, APPROVE (CE)) — `tests/reports/A-14-6.md`; звіти гейтів спроби 7 — `tests/reports/A-14-7.md`.

## Ревізія package/ (commit SHA)
`SHA: 1778db751161196b88a921005000c9b7f2162223`

## Прогін C-03
`SHA прогону: 1778db7` · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). `tools/odoo/` на чистих базах, Odoo 19.0 CE, uk_UA: `clean_db.sh` → `install.sh <модулі apply.py plan> --addons-src package/addons --lang uk_UA` → `run_tests.sh` (td_mebli_* — одним прогоном з турами; `td_knowledge`+`td_mebli_knowledge`, `td_support`, `td_home_menu` — окремо). Демо-шар: база B + `td_mebli_demo`, `/td_mebli_demo` (A-11-fix3).

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 47 модулів) | test-mebli-fix4-a11c-A (A-11-fix4, той самий код) | 349 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| light (`profiles/answers.alt-1.yaml`) | test-mebli-fix4-a147-c1-light | 333 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| B (`profiles/answers.alt-2.yaml`) | test-mebli-fix4-a147-c1-B | 354 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |

Формат клітинки — тестів / failed+error. Нові тести A-11-fix4: `test_app_icon` у td_knowledge, td_mebli_dashboard, td_mebli_measure (+1 кожен), td_home_menu `test_app_icons` (+2) і розширений тур; `td_mebli_demo` не змінювався (B + demo — A-15-full-3). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 1778db751161196b88a921005000c9b7f2162223 | 1778db7 success (локально) | APPROVE (замінники) | правок немає |
| ee | 1778db751161196b88a921005000c9b7f2162223 | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); змінені модулі EE-частини не мають, `depends` без EE/AGPL |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 0fbcd1d..1778db7) | APPROVE (замінник) | WARN: EE не перевірено | іконки — лише файли `static/description/` і `web_icon`; головний екран — власні OWL/SCSS/XML, без файлів `web_enterprise`; знахідок 0; info N7-1, N7-2 |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | нових прав, маршрутів, `sudo` немає; клас `body.td_home_menu_mode` знімається при виході з екрана (`onWillUnmount`); `t-esc` назв меню (без `t-raw`) |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | `package/config` не змінено; «Модулі до установки» ті самі (версії модулів — патч) |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | pylint-odoo (odoolint, E, F) 5 змінених модулів — у змінених файлах нових знахідок 0 (решта — давні, не з diff); ruff — нових 0 (F401 у `tests/__init__.py` — шаблон Odoo); `.pot`/uk.po — тексти не змінювались, `test_i18n_po` PASS |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-mebli-fix4-a147-c1-cv`: модулі 47 + конфіг (8/4/14) + майстер-дані 28/28 (97 записів) + compare diff 0 + read-back unchanged 26 + smoke OK; статей бази знань 8 |

## Покриття ALLOCATION
- `package/addons/`: обсяг diff — 5 модулів (`td_home_menu`, `td_knowledge`, `td_mebli_dashboard`, `td_mebli_measure`, `td_mebli_notify`); C-03 — усі встановлені `td_*` профілів A/light/B (мости EE — не перевірено).
- `package/config/`, `package/master-data/`: без змін; track-convergence на налаштованій базі A.
- Покриття 100 % (CE).

## Правки
Цикли спроб 1–6: №1–40 і D-18…D-21 закрито. У спробі 7 нових правок немає.

Закрито до гейтів (A-11-fix4, `1778db7`; джерело — завдання власника щодо вигляду, знімки `home-menu-review/before-*`):
| № | файл | опис | серйозність | статус |
|---|---|---|---|---|
| UI-1 | td_knowledge, td_mebli_dashboard, td_mebli_measure: static/description/icon.{svg,png}, меню | іконки з плашкою / чужа іконка `crm` → власні в стилі Odoo 19 | низький | закрито (1778db7) |
| UI-2 | td_home_menu: static/src/home_menu/* | «Обслуговуванн / я» → підпис в один рядок з «…» і `title`; вигляд як EE власним кодом | низький | закрито (1778db7) |
| T-1 | td_mebli_notify: tests/test_g1_notify.py | тести дат листів падали при запуску 22–24 UTC (північ Europe/Kyiv) → `freeze_time` | низький | закрито (1778db7) |

Info — не правки, без коду повернення:
- **N5-1, N5-2** — як у спробі 5; **N6-1…N6-3** — як у спробі 6 (AI-25, AI-26).
- **N7-1.** Режим головного екрана перевизначає CSS-змінні навбару (`--NavBar-entry-color…`) — тема з власними змінними може перекрити (AI-31); темну тему не перевіряли.
- **N7-2.** Довгі назви застосунків видно повністю лише в `title` (підказка) і в пошуку (AI-30).

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — спроба 7 на `1778db7`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Правок немає; зміни A-11-fix4 (UI-1, UI-2, T-1) — закрито.
- C-03 — success: локальний прогін на `1778db7` (A 388, light 372, B 393 тестів; 0 failed).
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
