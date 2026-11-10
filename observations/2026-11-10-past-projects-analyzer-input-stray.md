---
skill: flow-research:past-projects-analyzer
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли в docs/industries/<галузь>/_input/ поруч із sources.md лежать вхідні файли інших кроків (crm.csv для A-05) або README"
confidence: high
evidence: ["check_past_projects.py, stray_inputs(): будь-який видимий файл у _input/, крім sources.md, дає PP-input FAIL → waiting_human", "docs/industries/mebli/_input/ у тесті: README.md, crm.csv (A-05 segment-selector читає _input/crm.csv), sources.md — відновлює tests/restore-input.sh", "SKILL.md, таблиця входів: «на час A-04 там лише він»"]
repeat_of: null
siblings_checked: ["flow-research:segment-selector: same", "flow-research:demand-test-runner: ?"]
source: "tests/reports/A-04-1.md (тест mebli, етап 1)"
summary: PP-input вимагає в _input/ лише sources.md, а A-05 кладе туди crm.csv — сусідні кроки конфліктують
---
**Очікували:** `_input/` — спільна робоча тека галузі (sources.md для A-04, crm.csv для A-05, signals.csv/calls.md для A-23), і A-04 не провалюється через файли інших кроків.
**Отримали:** прогін 1 зупинився раніше (порожній sources.md), але в прогоні 2 PP-input дасть FAIL через README.md і crm.csv → `waiting_human` «прибрати сторонні файли», хоча crm.csv потрібен A-05.
**Пропозиція:** у stray_inputs() — allow-list відомих вхідних файлів флоу (crm.csv, signals.csv, calls.md, README.md) або перевіряти лише файли з ознаками ПДн/витягів; синхронно оновити `references/autochecks.md` (PP-input) і `sources-format.md`. Альтернатива — окремі підтеки `_input/A-04/`, `_input/A-05/` (рішення власника flow-research).
**Принцип:** спільна тека — спільний контракт: перевірка одного кроку не повинна забороняти входи сусіда.
