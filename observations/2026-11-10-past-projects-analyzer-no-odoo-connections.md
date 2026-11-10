---
skill: flow-research:past-projects-analyzer
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли наряд має odoo_connections: [] (тест без Odoo або крок без потреби в базі flow)"
confidence: medium
evidence: ["SKILL.md, Крок 0 п.2: «list_odoo_connections → звірити alias flow з allow-list наряду»", "tests/naryad/A-04.yaml: odoo_connections: []; CLAUDE.md тесту забороняє будь-який виклик odoo_*", "industry-scoring/SKILL.md, Крок 0 — той самий пункт"]
repeat_of: null
siblings_checked: ["flow-research:industry-scoring: same", "flow-research:segment-selector: ?", "flow-research:concept-mapper: ?"]
source: "tests/reports/A-04-1.md (тест mebli, етап 1)"
summary: Крок 0 вимагає list_odoo_connections, але не каже, що робити при порожньому allow-list
---
**Очікували:** явне правило: `odoo_connections: []` → odoo-mcp не викликати, пункт пропустити (SKIP у checks), бо скіл Odoo сам не читає.
**Отримали:** правила немає; у тесті пункт пропущено за CLAUDE.md, у checks — SKIP. В A-01 (industry-scoring) той самий пункт також пропущено без запису.
**Пропозиція:** у Кроці 0 обох скілів: «allow-list порожній → odoo_* не викликати; SKIP odoo-connections у checks»; за потреби — спільний рядок у `flow-core/references/data-and-connections.md`.
**Принцип:** порожній allow-list означає «жодного підключення», а не «перевір, що там».
