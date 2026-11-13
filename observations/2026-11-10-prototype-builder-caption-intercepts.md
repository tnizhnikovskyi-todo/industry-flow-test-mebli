---
skill: flow-research:prototype-builder
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли кнопка дії екрана опиняється під фіксованою панеллю підпису відео (#cap) оболонки prototype-shell.html"
confidence: high
evidence: ["перший прогін record.mjs у A-21: 6/6 сценаріїв FAIL — тайм-аут кліку, Playwright: «#cap intercepts pointer events»", "обхід виконавця: у всіх e2e/SC-*.spec.mjs кнопки натискаються Enter за тим самим data-testid замість click"]
repeat_of: null
siblings_checked: ["flow-package-build:demo-base-builder: ?"]
source: "tests/reports/A-21.md (тест mebli, етап 1)"
summary: Панель підпису відео в оболонці перехоплює кліки — сценарії проходять лише через Enter замість click
---
**Очікували:** spec-файли за `references/scenario-spec-template.md` (click за data-testid) проходять на оболонці скіла без обходів.
**Отримали:** фіксований `#cap` перекриває кнопки внизу сторінки; виконавець замінив click на Enter у 6 spec — перевірка кроків та сама, але це відхилення від шаблону.
**Пропозиція:** у `references/prototype-shell.html` — `pointer-events: none` для `#cap` (або відступ знизу під висоту панелі); у self-test record.mjs — кейс із кнопкою внизу сторінки.
**Принцип:** службовий шар відео не повинен змінювати поведінку інтерфейсу, яку перевіряє сценарій.
