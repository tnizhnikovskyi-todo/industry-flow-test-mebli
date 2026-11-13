# Звіт кроку A-20c, повний обсяг — тестовий режим, замість message_post

Наряд: `tests/naryad/A-20c-full.yaml`. Виконавець — `flow-executor-content`; правка CSS (перенос довгих позначок), перевірки, знімки, публікація, коміт, PR — runner.

```yaml
run: {step: A-20c, scope: package/mebli, attempt: 1, started: 2026-11-12T05:20:00Z, finished: 2026-11-12T05:50:00Z}
result: waiting_human
sample: false
waiting_for: {role: Власник продукту, what: "гейт концепції A-20c: «Затвердити / Повернути» (gate.return_to: A-20 / A-03b / A-03c) + відповіді на 5 питань сторінки", resume: {step: A-21, note: "A-21 не стартує до перевірки на чистих базах (№13, запис 30)"}}
pr: "див. PR гілки flow/A-20c-full-test"
published: https://claude.ai/artifact/RMKQLpFxP6D2cwzkCCDakD   # версія 2, full; приватний
skill_versions: {"flow-research:concept-presentation": "0.2.0", "flow-core:flow-autocheck": "0.2.0"}
model: {primary: null, review: null}
usage: {tokens_in: 360000, tokens_out: 60000, cost_usd: 9, agent_hours: 0.4}   # оцінка
cost_estimated: true
base_sha: 2311a95
checks:
  - {id: OP-pages/nav/anchors/contract, status: PASS, msg: "без --sample, 3 сторінки"}
  - {id: OP-target, status: WARN, msg: "index.html 85 KB (> 60 KB): логотип ≈11 KB + повний обсяг"}
  - {id: BR-*, status: PASS, msg: "3 сторінки"}
  - {id: PRV-pii, status: PASS, msg: "--pages owner-page"}
  - {id: INT-dup, status: PASS}
  - {id: FACT-mismatch, status: PASS, msg: "--require-markers, 3 сторінки"}
  - {id: FACT-orphan, status: WARN}
  - {id: playwright-390-1280, status: PASS, msg: "після правки .tag (перенос) — без горизонтального скролу на 3 сторінках"}
rejected_count: 13
rejected_ref: docs/industries/mebli/research/REJECTED.md
memo: |
  Кнопки (5 відкритих): G-60, OB8-21, OB8-14, G-65, G-61; списком — №9, №22; вирішені 2026-11-12 (A-03c, №13, №16, G-66, G-58) — згорнуто без кнопок.
  Невпевнений:
  - G-60 лишено відкритим (запис 32 «не вирішено, діє замовчування»).
  - Для цін 1,0 і 2,0 млн у таблиці окупності немає ключів facts.yaml — подано словами; прогалина для A-20.
  - Групування 46 систем на competitors і групи матриці — AI, позначено на сторінці; розділ цитат конкурентів без цитат (sources-log без SRC-NNN).
  - Зовнішніх посилань на джерела немає (PAGE-CONTRACT): джерела названо текстом.
  - Розділ #current — з prototype-real/PLAN.md з позначкою «буде перезібрано (№19)».
  - Стара повна сторінка R18 (4US1Hk8R2AkJMN2LbZU675) не оновлювалась — застаріла; видалення чи оновлення — рішення власника.
observations: []
```
