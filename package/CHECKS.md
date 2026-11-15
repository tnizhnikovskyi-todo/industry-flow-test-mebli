# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 5, цикл 2, 2026-11-15)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); записи 48, 51; `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка` (`params.mode`), версія флоу 2. Причина — контур коду 1 (TEST-START §(д) 12b): після гейтів `21afe46` у `package/` з'явились модулі §27/§27а `td_home_menu`, `td_support`, `td_knowledge`, `td_mebli_knowledge` (A-11-fix: версія `td_mebli_knowledge`), A-12-fix — «Модулі до установки». Обсяг: `git diff 21afe46..13bb66d -- package/addons package/config package/master-data` (72 файли, +4859/−1). Цикл 1 (`13bb66d`) — правки F-38…F-40 → A-11; виправлено в цій гілці (A-11-fix2, `795f6b1`, `tests/reports/A-11-fix2.md`); цикл 2 — гейти на `795f6b1` (обсяг циклу 2: `git diff 13bb66d..795f6b1 -- package/`, 12 файлів, +40/−20; вердикти pr/security/lint — за повним обсягом `21afe46..795f6b1`). Повні звіти гейтів — `tests/reports/A-14-5.md`.

## Ревізія package/ (commit SHA)
`SHA: 795f6b11d984e7048e0aec1cdd04125d4a559f2a`

## Прогін C-03
`SHA прогону: 795f6b1` · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). `tools/odoo/` на чистих базах, Odoo 19.0 CE, uk_UA: `clean_db.sh` → `install.sh <модулі apply.py plan> --addons-src package/addons --lang uk_UA` → `run_tests.sh` (td_mebli_* — одним прогоном з турами; `td_knowledge`+`td_mebli_knowledge`, `td_support`, `td_home_menu` — окремо).

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 47 модулів) | test-pkg-mebli-a145-c2-A | 333 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |
| light (`profiles/answers.alt-1.yaml`) | test-pkg-mebli-a145-c2-light | 317 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |
| B (`profiles/answers.alt-2.yaml`) | test-pkg-mebli-a145-c2-B | 338 / 0 (skipped 1) | 17 / 0 | 15 / 0 | 4 / 0 |

Формат клітинки — тестів / failed+error. Цикл 1 (`13bb66d`): `failure` — 1 тест `td_mebli_knowledge` у кожному профілі (F-38). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 795f6b11d984e7048e0aec1cdd04125d4a559f2a | 795f6b1 success (локально) | APPROVE (замінники) | цикл 1: F-38…F-40 → A-11, закрито в A-11-fix2 |
| ee | 795f6b11d984e7048e0aec1cdd04125d4a559f2a | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); нові модулі EE-частини не мають, `depends` без EE/AGPL |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 21afe46..795f6b1) | APPROVE (замінник) | WARN: EE не перевірено | цикл 1 — правки F-38, F-39; цикл 2 — закрито, нових знахідок 0 |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | публічних маршрутів немає; права/правила записів `td.support.request`, `td.knowledge.article` — за README; F-40 закрито; info N5-1 (без `company_id`) |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | A-12-fix: порядок модулів — порушень 0; `td_home_menu` лише `ce`; A-11-fix2 — лише коментарі залежностей |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | pylint-odoo усіх `td_*` 9.73/10, E/F 0; ruff 175 → 186 (+11 стиль, усі в тестах і `stemmer.py`; F401 прибрано); uk.po — тести `test_i18n_po` PASS |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-pkg-mebli-a145-c2-cv`: модулі 47 + конфіг (8/4/14) + майстер-дані 28/28 (97 записів) + compare diff 0 + read-back 23/23 + smoke OK; статей бази знань 8 |

## Покриття ALLOCATION
- `package/addons/`: усі 29 модулів у обсязі pr-review/lint (`td_mebli_*` 25 + §27/§27а `td_home_menu`, `td_support`, `td_knowledge`, `td_mebli_knowledge` — ALLOCATION їх не вимагає); C-03 — усі встановлені `td_*` профілів A/light/B (мости EE — не перевірено).
- `package/config/`: CONFIG.md, manifest.yaml, vp-map.yaml, install-log.md, data/ (7 файлів) — config-review і track-convergence.
- `package/master-data/`: 28 CSV за README — track-convergence (тест-імпорт 28/28).
- Покриття 100 % (CE).

## Правки
Цикли 1–4 (671b39c, 935b591, a5a1063, 21afe46): №1–37 закрито.

| № | джерело | файл:рядок | опис | серйозність | код | статус |
|---|---|---|---|---|---|---|
| F-38 | C-03, pr-review | td_mebli_knowledge/__manifest__.py:12; data/td_knowledge_article_data.xml:44,64,84,103 | Прив'язка статей до екранів (`model_ids` search за `ir.model`) залежить від порядку установки: `depends` лише `td_knowledge`, `td_mebli_base` — модулі екранів (`td_mebli_measure`, `_cutting`, `_install`, `_claim`) ставляться пізніше, search порожній, а `noupdate` не виправить. На A/light/B без статті лишаються різні екрани | major | A-11 | закрито (795f6b1) |
| F-39 | pr-review | td_knowledge/models/td_knowledge_article.py:109-112 | `_td_ancestors` читає назви розділів без перевірки доступу: відкрита стаття в розділі, обмеженому групами, — AccessError у читача й «Довідці» | minor | A-11 | закрито (795f6b1) |
| F-40 | security-review, lint | td_support/models/td_support_request.py:11,197 | контакт іде в заголовок `Reply-To` без прибирання переносів рядка (лист падає при побудові); невикористаний імпорт `escape` | minor | A-11 | закрито (795f6b1) |

Info — не правки, без коду повернення:
- **N5-1.** `td.support.request` і `td.knowledge.article` без `company_id`: при кількох юрособах (VP-03 multi) звернення й статті спільні для бази. Свідомо за README модулів; розділення — рішення власника.
- **N5-2.** `td_reader_tree` читає всі доступні статті (`search([])`, pylint no-search-all) — для бази знань пакета прийнятно.

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — цикл 2 на `795f6b1`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Цикли: 1 — правки → A-11 (F-38 major, F-39, F-40 minor); 2 — APPROVE, відкритих правок 0.
- C-03 — success: локальний прогін на `795f6b1` (A 369, light 353, B 374 тестів; 0 failed).
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
