# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 5, цикл 1, 2026-11-15)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); записи 48, 51; `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка` (`params.mode`), версія флоу 2. Причина — контур коду 1 (TEST-START §(д) 12b): після гейтів `21afe46` у `package/` з'явились модулі §27/§27а `td_home_menu`, `td_support`, `td_knowledge`, `td_mebli_knowledge` (A-11-fix: версія `td_mebli_knowledge`), A-12-fix — «Модулі до установки». Обсяг: `git diff 21afe46..13bb66d -- package/addons package/config package/master-data` (72 файли, +4859/−1). Повні звіти гейтів — `tests/reports/A-14-5.md`.

## Ревізія package/ (commit SHA)
`SHA: 13bb66dbd260d3e8ed204b0ea853b8f6d569aae5`

## Прогін C-03
`SHA прогону: 13bb66d` · статус: `failure` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; `tools/odoo/run_tests.sh` на чистих базах, Odoo 19.0 CE, uk_UA). Тести всіх встановлених `td_*` профілю (td_mebli_* — одним прогоном з турами; `td_knowledge`+`td_mebli_knowledge`, `td_support`, `td_home_menu` — окремо):

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`) | test-pkg-mebli-a145-c1-A | 333, **1 failed** | 16, **1 failed** | 14 / 0 | 4 / 0 |
| light (`profiles/answers.alt-1.yaml`) | test-pkg-mebli-a145-c1-light | 317, **1 failed** | 16, **1 failed** | 14 / 0 | 4 / 0 |
| B (`profiles/answers.alt-2.yaml`) | test-pkg-mebli-a145-c1-B | 338, **1 failed** | 16, **1 failed** | 14 / 0 | 4 / 0 |

Падає один тест — `td_mebli_knowledge` `test_articles_linked_to_installed_screens` (F-38). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 13bb66dbd260d3e8ed204b0ea853b8f6d569aae5 | 13bb66d failure (локально) | правки → A-11 | F-38 major, F-39, F-40 minor |
| ee | 13bb66dbd260d3e8ed204b0ea853b8f6d569aae5 | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); нові модулі EE-частини не мають |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 21afe46..13bb66d) | правки (замінник) | WARN: EE не перевірено | F-38 (major), F-39 (minor) |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | правки (замінник) | WARN: EE не перевірено | F-40 (minor). Публічних маршрутів у нових модулях немає; права й правила записів — див. звіт |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | A-12-fix: порядок модулів — порушень 0; `td_home_menu` лише `ce`; чиста база A: apply/compare/read-back 23/23 |
| odoo19-lint | замінник `boost:odoo19-lint` | правки (замінник) | WARN: EE не перевірено | pylint-odoo нових модулів 9.42/10, E 0; ruff +12 (1 F401 `escape` — у F-40) |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | не виконано: гейти pr-review/config-review не APPROVE | WARN: EE не перевірено | інформативно прогнано: база A — модулі + конфіг + майстер-дані 28/28 + compare diff 0 + read-back 23/23 + smoke OK |

## Правки
Цикли 1–4 (671b39c, 935b591, a5a1063, 21afe46): №1–37 закрито.

| № | джерело | файл:рядок | опис | серйозність | код | статус |
|---|---|---|---|---|---|---|
| F-38 | C-03, pr-review | td_mebli_knowledge/__manifest__.py:12; data/td_knowledge_article_data.xml:44,64,84,103 | Прив'язка статей до екранів (`model_ids` search за `ir.model`) залежить від порядку установки: `depends` лише `td_knowledge`, `td_mebli_base` — модулі екранів (`td_mebli_measure`, `_cutting`, `_install`, `_claim`) ставляться пізніше, search порожній, а `noupdate` не виправить. На A/light/B без статті лишаються різні екрани | major | A-11 | відкрито |
| F-39 | pr-review | td_knowledge/models/td_knowledge_article.py:109-112 | `_td_ancestors` читає назви розділів без перевірки доступу: відкрита стаття в розділі, обмеженому групами, — AccessError у читача й «Довідці» | minor | A-11 | відкрито |
| F-40 | security-review, lint | td_support/models/td_support_request.py:11,197 | контакт іде в заголовок `Reply-To` без прибирання переносів рядка (лист падає при побудові); невикористаний імпорт `escape` | minor | A-11 | відкрито |

## Зведений вердикт
**правки → A-11** (цикл 1). Виправлення — у цій же гілці (`tests/reports/A-11-fix2.md`), далі цикл 2.
