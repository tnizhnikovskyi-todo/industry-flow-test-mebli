# CHECKS.md — автоперевірки пакета «меблі» (A-14, спроба 9, 2026-11-16)

Гейти виконано **замінниками** (скіли організації `odoo19-mvp-build:*`, `boost:odoo19-lint`, CI C-03 у сесії недоступні; рішення власника — запис 52 `flow/decisions.md`, варіант (а); `observations/2026-11-13-a14-gates-substitutes.md`). Режим `перевірка`. Причина — рішення власника 2026-11-16: обмін з BAS/BAF **виключено** з пакета (`flow/decisions.md` рядок 55), нова іконка «Керівник» (рядок 56), технолог — «Виключити для», видалення — лише адміністратор, технолог архівує (рядок 57). A-11-fix6 (`package/deferred/` видалено; `td_mebli_base` 19.0.1.1.4 — міграція старих баз, AI-42; `td_mebli_install` — хелпер AC-042 прибрано; `td_mebli_mrp` 19.0.1.1.7 — D-24, AI-43; `td_mebli_dashboard` 19.0.1.1.4 — іконка; `td_mebli_migration`, `td_mebli_sale` — тексти), A-12-7 (VP-04, PF-03, PF-10 прибрано; Q-04 вилучено), A-13-6 (README). Обсяг: `git diff 2733ccc..09fc902 -- package/`.

## Ревізія package/ (commit SHA)
`SHA: 09fc902be78a3a4706f17cfad24beb9e9bb83994`

## Прогін C-03
`SHA прогону: 2c5c8b8` (цикл 2; `09fc902` відрізняється від нього лише коментарем `td_mebli_base/migrations/19.0.1.1.4/end-migrate.py`) · статус: `success` (замінник: локальний прогін, не CI — `.github/workflows/ci.yml` немає; рядок C-03 для Архітектора — MANUAL, AI-A14-01). `tools/odoo/` на чистих базах, Odoo 19.0 CE, uk_UA, окремий каталог доставки `/home/user/odoo19/delivery-bas2` (лише `package/addons`, без модулів обміну): `clean_db` → `install.sh` (модулі `apply.py plan` профілю) → `run_tests.sh`; профілі паралельно, конфіги `odoo-tools-bas2{,-light,-B}.conf` (порти 8297–8299).

| профіль | база | td_mebli_* | td_knowledge (+mebli) | td_support | td_home_menu |
|---|---|---|---|---|---|
| A (`answers.example.yaml`, 45 модулів) | test-mebli-bas2-a149-A | 328 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| light (`profiles/answers.alt-1.yaml`, 45) | test-mebli-bas2-a149-light | 328 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |
| B (`profiles/answers.alt-2.yaml`, 46) | test-mebli-bas2-a149-B | 333 / 0 (skipped 1) | 18 / 0 | 15 / 0 | 6 / 0 |

Формат клітинки — тестів / failed+error (цикл 2). Кількість та сама, що в спробі 8: мінус `test_ac_021_cancel_marks_helper` (хелпер AC-042 прибрано), плюс `test_d24_technologist_keeps_exclusions_and_archives` (D-24); `test_d23_…` доповнено (рядок атрибута технолога архівується). Цикл 1 (`3c61e8b`…`4ccd5a3`): A і light — 1 failed (`td_mebli_base` `test_d16_pot_and_uk_po_cover_every_exported_text`: у `td_mebli_mrp.pot` немає «Product Variant» — новий `_inherit = product.product`), B не запускався → правка №41. Модулів обміну в жодній базі немає (`hr_attendance` — installed). Бази видалено.

## Редакції
`editions: both` (OWNER-INTAKE).
| edition | SHA | C-03 (SHA прогону, статус) | вердикт | примітка |
|---|---|---|---|---|
| ce | 09fc902be78a3a4706f17cfad24beb9e9bb83994 | 2c5c8b8 success (локально, цикл 2) | APPROVE (замінники) | правка №41 закрита в циклі 2 |
| ee | 09fc902be78a3a4706f17cfad24beb9e9bb83994 | не запущено | WARN: EE не перевірено | EE недоступна (ВП-4); змінені модулі EE-частини не мають, `depends` без EE/AGPL |

## Гейти
| гейт | команда або скіл | вердикт ce | вердикт ee | примітка |
|---|---|---|---|---|
| pr-review | замінник `odoo19-mvp-build:pr-review` (diff 2733ccc..09fc902) | APPROVE (замінник) | WARN: EE не перевірено | grep збірки: `depends`/моделі/поля/виклики модулів обміну — 0, `package/deferred/` немає; `td_mebli_base` end-migrate — лише стан модулів обміну й `DROP TABLE IF EXISTS` трьох фіксованих таблиць, коли коду модуля немає; перевірено на старій базі (код `2733ccc` + модулі обміну) у двох випадках — без коду і зі старою доставкою: RC 0, модулі uninstalled, `ir.model.data`/поля/колонки/таблиці/подання 0, форми 10 моделей відкриваються (A-11-fix6); хелпер AC-042 без викликів прибрано |
| security-review | замінник `odoo19-mvp-build:security-review` (статично) | APPROVE (замінник) | WARN: EE не перевірено | нова ACL групи «Технолог» — `product.template.attribute.exclusion` read/write/create без unlink (рішення власника, рядок 57); `product.product._unlink_or_archive` для технолога без права unlink: `check_access('write')` перед `sudo()`, пише лише `active=False` (AI-43); правил записів не додано; видалення — лише адміністратор (тест `test_d24` — AccessError на unlink виключення, операції, специфікації, робочого центру, товару) |
| config-review | замінник `odoo19-mvp-build:config-review` | APPROVE (замінник) | WARN: EE не перевірено | VP-04 прибрано зі схеми, `vp-map.yaml`, прикладів і профілів; PF-03, PF-10 прибрано, інші PF без змін; `apply.py plan` 7 профілів — `unknown_keys` 0; старий ключ `VP-04` → `unknown_keys` (не застосовується); Q-04 вилучено з анкети; `ac` VP-05 без AC-042 |
| odoo19-lint | замінник `boost:odoo19-lint` | APPROVE (замінник) | WARN: EE не перевірено | ruff (E,F,W,B,I) змінених .py — нових знахідок 0 (давні I001/B017 у `td_mebli_install`); `.pot`/uk.po `td_mebli_mrp` + «Product Variant» / «Варіант товару» (uk.po Odoo 19 `product`) — test_d13/test_d16 PASS у циклі 2 |
| track-convergence | замінник `odoo19-mvp-build:track-convergence` | APPROVE (замінник) | WARN: EE не перевірено | база A `test-mebli-bas2-a149-cv` (цикл 1; i18n-правка №41 конфіг і імпорт не зачіпає): модулі 45 + конфіг (8/4/14; повтор unchanged 26) + майстер-дані 25/25 (91 запис) + compare diff 0 + read-back 22/0 (VP-04 більше немає) + smoke OK; кроків імпорту в базі 25 |

## Покриття ALLOCATION
- `package/addons/`: обсяг diff — 6 змінених модулів (`td_mebli_base`, `_install`, `_migration`, `_sale`, `_mrp`, `_dashboard`) і `package/deferred/` видалено (AC-039…AC-042, AC-078, AC-109 — «виключено рішенням власника 2026-11-16», не «не пройдено»); C-03 — усі встановлені `td_*` профілів A/light/B.
- `package/config/`, `package/master-data/`: змінено (A-12-7, A-13-6); track-convergence на налаштованій базі A.
- Покриття 100 % (CE) для AC збірки; виключені AC поза пакетом за рішенням власника.

## Правки
Цикли спроб 1–8: №1–40, D-18…D-21, UI-1, UI-2, T-1 закрито.
- **№41 (A-11, закрито в циклі 2).** `td_mebli_mrp` 19.0.1.1.7: новий `_inherit = 'product.product'` (D-24) додає до експорту перекладів назву моделі «Product Variant», якої не було в `td_mebli_mrp.pot`/`uk.po` → `test_d16_pot_and_uk_po_cover_every_exported_text` FAIL (A, light). Виправлено комітом `2c5c8b8` (+ «Варіант товару» з uk.po Odoo 19 `product`); `09fc902` — коментар end-migrate без назви моделей обміну. Цикл 2 — 0 failed.

Info — не правки, без коду повернення:
- **N9-1.** Профілі light і A однакові за модулями (як у спробі 8).
- **N9-2.** Оновлення старої бази з модулями обміну перевірено на синтетичній базі (A-11-fix6), не на базі клієнта (AI-42 — «ризик, перевірити на пілоті»).

## Зведений вердикт
`APPROVE (CE); EE не перевірено` — спроба 9 на `09fc902`, замінники за рішенням власника (запис 52 `flow/decisions.md`, варіант (а)).
- Правка №41 (A-11) закрита в циклі 2; обмін з BAS/BAF виключено рішенням власника 2026-11-16 (`flow/decisions.md` рядок 55).
- C-03 — success: локальний прогін цикл 2 (A 367, light 367, B 372 тестів; 0 failed).
- EE — `WARN: EE не перевірено` (ВП-4). Рішення «випускаємо з неперевіреною EE» — людина на A-17/A-18.
