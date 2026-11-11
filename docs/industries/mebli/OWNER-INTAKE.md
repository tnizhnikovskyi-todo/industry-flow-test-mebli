# Анкета власника — меблі (A-02b, OWNER-INTAKE.md)

Режим `prepare`, 2026-11-11. Наряд `tests/naryad/A-02b.yaml`. Шаблон — `owner-questionnaire/references/owner-intake-template.md` (0.2.0).
Анкету складено **після** рішень власника 2026-11-11 (`flow/decisions.md`, рядки 4–27): значення з цих рішень підставлено й позначено в «Журналі змін»;
решта — замовчування «меблів» із шаблона; невирішене — `уточнити`. AI нічого не вирішує за власника: власник підтверджує або змінює (≈10 хв — більшість уже вирішено).

```yaml
editions: both                  # * ce|ee|both — CE основа, EE апгрейд (рішення №3б, №12)
ee_bridges: now                 # * now|later — мости EE з першого релізу (рішення №12)
demo_edition: ce                # * ce|ee — зріз A-21 на CE (замовчування шаблона; A-21-real знято на CE)
market:
  country: Україна
  language: uk
  localization: l10n_ua
  accounting_system: BAS/BAF    # рішення №5
  accounting_mode: exchange     # рішення №5: «BAS/BAF клієнта + наш обмін»
icp:
  min_employees: 10             # рішення №3а; смуга 6–9 людей — відкрите питання (див. «Примітки»)
  revenue_min: 0                # замовчування шаблона
  legal_forms: [ТОВ, ФОП]       # замовчування шаблона
  light_tariff_fop: true        # рішення №4
ambition:
  scope: full                   # рішення №0: «Одразу повний пакет»
  evidence_gate: risk           # замовчування шаблона (К-01)
  company_marking: false        # рішення №2: розмітку 60 компаній не робимо
  trials: deferred              # рішення №6
  sessions_a05_a06: false       # замовчування шаблона
pricing:
  ce_entry: true                # рішення №3б
  ee_upgrade: true              # рішення №3б
  box_fixed_price: "коробка A"  # рішення №15; ціну A власник ще не назвав (параметр до A-23)
  pilot: "платний зі знижкою"   # рішення №20: «Платний пілот зі знижкою за кейс»
todo_data:
  allowed_sources: [crm, fathom, unitalk, aikb, gmail, own-erp]   # замовчування шаблона; рішення №18 — першоджерела лише після рішення про підставу обробки
  mode: read
  internal_raw_storage: repo-sources   # research/sources/ уже в репо галузі (START-HERE.md §1); формально рішення №22 відкрите
  push_deidentified: уточнити          # рішення №22 відкрите
do_not_reject:
  items: [конфігуратор, обрізки, міграція даних, дашборд керівника, кілька юросіб, премії/штрафи, якість з фото, NP-02, P-07, D-10, N-04, N-07, P-01 спрощ., C-03, C-04, F-11/S-09, D-16, S-01]
  class_rule: "усе, що є у ≥N конкурентів або було в попередній концепції"
  n: 3
licenses:
  own_modules: LGPL-3           # замовчування, НЕ рішення (рішення №14 відкрите)
  oca: idea                     # нотатка власника до №14: OCA — лише ідеї, не залежність
reuse:
  repos: []                     # уточнити — див. «Примітки», пропозиція AI
  projects: []                  # уточнити — див. «Примітки», пропозиція AI
brand:
  materials: ToDo
  demo_client: вигаданий
  white_label: false
materials:
  formats: [video_16x9, reels_9x16, mobile, one_pager]
  languages: [uk]
prototype:
  fidelity: real-slice          # A-21-real (prototype-real/) — реальний зріз
  new_record_in_frame: false
legal_ambiguous:
  to_answers_yaml: true         # узгоджено з рішенням №17 (обидва режими договору — параметром пакета)
rounds:
  review_max: 2
  review_control: 1
  human_target: 2
```

## Журнал змін

| Дата | Поле | Було | Стало | Джерело (повідомлення/задача) |
|---|---|---|---|---|
| 2026-11-11 | (усі поля) | — | замовчування шаблона 0.2.0 | `owner-intake-template.md`; галузь та сама (меблі) — галузеві замовчування збережено |
| 2026-11-11 | editions | both | both (підтверджено) | `flow/decisions.md` запис 8 (№3б), запис 16 (№12) |
| 2026-11-11 | ee_bridges | now | now (підтверджено) | `flow/decisions.md` запис 16 (№12 «Одразу») |
| 2026-11-11 | market.accounting_system / accounting_mode | BAS/BAF / exchange | BAS/BAF / exchange (підтверджено) | `flow/decisions.md` запис 10 (№5) |
| 2026-11-11 | icp.min_employees | 10 | 10 (підтверджено) | `flow/decisions.md` запис 7 (№3а) |
| 2026-11-11 | icp.light_tariff_fop | true | true (підтверджено) | `flow/decisions.md` запис 9 (№4) |
| 2026-11-11 | ambition.scope | full | full (підтверджено) | `flow/decisions.md` запис 4 (№0) |
| 2026-11-11 | ambition.company_marking | false | false (підтверджено) | `flow/decisions.md` запис 6 (№2) |
| 2026-11-11 | ambition.trials | deferred | deferred (підтверджено) | `flow/decisions.md` запис 11 (№6) |
| 2026-11-11 | pricing.ce_entry / ee_upgrade | true / true | true / true (підтверджено) | `flow/decisions.md` запис 8 (№3б) |
| 2026-11-11 | pricing.box_fixed_price | «коробка A» | «коробка A» (підтверджено) | `flow/decisions.md` запис 19 (№15) |
| 2026-11-11 | pricing.pilot | «платний зі знижкою» | «платний зі знижкою» (підтверджено) | `flow/decisions.md` запис 24 (№20) |
| 2026-11-11 | todo_data.push_deidentified | true | уточнити | `flow/decisions.md` запис 26 (№22 «не вирішено») — замовчування суперечить відкритому рішенню, не підставляємо |
| 2026-11-11 | do_not_reject.items | 7 позицій шаблона | + 11 позицій, повернених власником | `flow/decisions.md` запис 27 (повернення 11 позицій, R17; `REJECTED.md` §4а) — AI пропонує захистити їх від відкидання; підтвердити |
| 2026-11-11 | licenses.oca | idea | idea (підтверджено нотаткою) | `flow/decisions.md` запис 18 (нотатка до №14) |
| 2026-11-11 | reuse.repos / reuse.projects | [] | [] (уточнити) | рішення власника немає; пропозиція AI — у «Примітках» |

«запис N» — значення колонки «№» у `flow/decisions.md`; «№X» — номер рішення в OWNER-BRIEF §8.

## Примітки

**Що потрібно від власника (≈10 хв):**
1. `reuse.repos` / `reuse.projects` — **блокує A-03c** (`validate` не пройде з `[]`). Пропозиція AI з A-04 (`past-projects.md`):
   `repos: [tnizhnikovskyi-todo/todo_timur]` (модулі `factory3d/odoo_addons`, П-01, Odoo 19) і `projects: [П-01, own-erp]`
   (`own-erp` — перелік модулів продуктивної бази ToDo, Odoo 18: авансові рахунки, платіжний календар, договори, виписки, курс НБУ).
   Інших репо ToDo з модулями Odoo AI не знає — назвіть їх або поставте `"—"`.
2. `todo_data.push_deidentified` — пов'язано з відкритим рішенням №22 (`research/sources/` у git). Рекомендація AI (як у OWNER-BRIEF §8): `true` для знеособлених версій, сирі — окремо.
3. `do_not_reject.items` — підтвердити, що 11 повернених позицій (R17) захищені від відкидання так само, як 7 позицій шаблона.
4. Решта полів — підтвердити мовчки (взято з ваших рішень 2026-11-11 або замовчування «меблів»).

**Що анкета НЕ вирішує (відкриті рішення лишаються відкритими):** №9 (ціна EE; для розрахунків — €27,90), №13 (перевірка на чистих базах),
№14 (ліцензія td_: `own_modules: LGPL-3` — лише замовчування), №16 (склад першого релізу й коробки A), №21 (пороги A-23 і календар),
№22 (`sources/` у git), смуга 6–9 людей (між легким тарифом ФОП і порогом ICP 10). Окремих полів анкети для них немає — питання не дублюються (`INT-dup`).

**Відомі розбіжності:** `todo_data.allowed_sources` — замовчування шаблона; рішення №18 обмежує першоджерела до рішення про підставу обробки (до того — лише агрегати).
Поле переліку не має значення «лише агрегати», тому обмеження записано тут, а не в YAML.
