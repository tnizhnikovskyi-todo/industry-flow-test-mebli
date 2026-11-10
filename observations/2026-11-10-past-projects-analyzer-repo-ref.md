---
skill: flow-research:past-projects-analyzer
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли код проєкту лежить не на гілці за замовчуванням репозиторію з колонки «репозиторії» sources.md"
confidence: high
evidence: ["sources.md П-01: репозиторій todo_timur/factory3d без гілки", "гілка за замовчуванням (adce004): лише factory3d_iot_sim; інтеграційна гілка claude/factory3d-build (0976f05): 37 модулів td_* — за factory3d/build/BUILD_STATUS.md", "sources-format.md: колонки гілки/ref немає; SKILL.md Крок 5 гілку не згадує"]
repeat_of: null
siblings_checked: ["odoo19-mvp-build:reverse-spec: ?"]
source: "tests/reports/A-04-2.md (тест mebli, етап 1)"
summary: sources.md не має колонки гілки/ref — агент сам обрав інтеграційну гілку за журналом збірки
---
**Очікували:** `sources.md` фіксує ref (гілку/тег/SHA) коду проєкту, і скіл читає саме його.
**Отримали:** колонки немає; на гілці за замовчуванням — 1 модуль, а 37 модулів — на гілці `claude/factory3d-build`, яку агент знайшов через BUILD_STATUS.md і обрав сам (рішення в memo, ідентифікатори `@0976f05`).
**Пропозиція:** у `sources-format.md` — формат «репозиторій@ref» у колонці «репозиторії» (або окрема колонка «ref»), у check_past_projects.py — розбір ref; у Кроці 5 SKILL.md — «немає ref → гілка за замовчуванням, інші гілки не шукати; знайдено згадку іншої гілки → у Прогалини / memo».
**Принцип:** джерело коду фіксується ref'ом людиною, а не вибором агента.
