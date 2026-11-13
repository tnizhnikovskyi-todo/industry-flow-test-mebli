---
skill: flow-research:prototype-builder
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли наряд A-21 має odoo_connections: [] замість «лише flow»"
confidence: medium
evidence: ["SKILL.md Крок 0: «odoo_connections = лише flow»; зупинка описана лише для зайвих підключень", "tests/naryad/A-21.yaml: odoo_connections: []; TEST-START.md очікував можливу зупинку"]
repeat_of: null
siblings_checked: ["flow-research:past-projects-analyzer: same", "flow-research:industry-scoring: same"]
source: "tests/reports/A-21.md (тест mebli, етап 1)"
summary: Крок 0 вимагає «лише flow», поведінка на порожньому allow-list не описана — трактовано як «зайвих немає»
---
**Очікували:** явне правило для `odoo_connections: []` (скіл сам Odoo не викликає — продовжувати).
**Отримали:** скіл не зупинився (порожній список не містить зайвих підключень), правило виведено виконавцем.
**Пропозиція:** спільний рядок у `flow-core/references/data-and-connections.md`: «порожній allow-list = жодних викликів odoo_*; крок, якому Odoo не потрібен, продовжує» — і посилання на нього з Кроку 0 скілів flow-research.
**Принцип:** —
