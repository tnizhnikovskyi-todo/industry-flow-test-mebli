---
skill: flow-research:prototype-builder
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли screens.md (A-20) використовує типи «календар» або «зведена таблиця» з concept-mapper/references/screen-types.md"
confidence: high
evidence: ["docs/industries/mebli/concept/screens.md: S-07, S-12 — календар; S-10 — зведена таблиця; S-11 — зведення", "prototype-shell.html має рендерери лише list/form/kanban/dashboard/wizard — S-07, S-10, S-11, S-12 показано списками"]
repeat_of: null
siblings_checked: ["flow-research:concept-mapper: same"]
source: "tests/reports/A-21.md (тест mebli, етап 1)"
summary: Оболонка прототипу не має календаря й зведеної таблиці, хоча concept-mapper пропонує ці типи
---
**Очікували:** кожен тип подання з `screen-types.md` (A-20) має рендерер в оболонці A-21.
**Отримали:** календар і зведена таблиця показані як список — сценарії проходять, але вигляд не відповідає концепції.
**Пропозиція:** або додати в оболонку рендерери «календар» і «зведена таблиця», або в `screen-types.md` позначити, що A-21 показує їх списком (формати сусідніх кроків узгодити парою).
**Принцип:** перелік типів у концепції = перелік рендерерів прототипу.
