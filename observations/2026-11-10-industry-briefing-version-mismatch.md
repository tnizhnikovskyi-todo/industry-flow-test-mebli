---
skill: odoo19-discovery-initiation:industry-briefing
date: 2026-11-10
status: open
kind: gap
fix: unknown
rule: "коли skill_ref наряду вказує версію скіла організації, а в сесії встановлена інша"
confidence: high
evidence: ["tests/naryad/A-03.yaml: skill_ref industry-briefing@0.12.1 (з marketplace.json)", "плагін odoo19-discovery-initiation у хмарній сесії: plugin.json version 0.10.0"]
repeat_of: null
siblings_checked: []
source: "tests/reports/A-03.md (тест mebli, етап 1)"
summary: Наряд просить industry-briefing 0.12.1, у сесії встановлено 0.10.0 — крок виконано на іншій версії
---
**Очікували:** версія скіла організації в сесії = `skill_ref` наряду (або runner зупиняється за правилом C-06).
**Отримали:** встановлено 0.10.0; за CLAUDE.md тесту версію лише зафіксовано у звіті, крок виконано. Чим 0.10.0 відрізняється від 0.12.1 (зокрема щодо «структури відділів» і `where`) — невідомо.
**Пропозиція:** з'ясувати, чому каталог організації віддає 0.10.0 (кеш синхронізації чи marketplace.json випереджає публікацію); для етапу 2 — перевірка версії скілів організації в runner як FAIL/ескалація, а не лише запис.
**Принцип:** —
