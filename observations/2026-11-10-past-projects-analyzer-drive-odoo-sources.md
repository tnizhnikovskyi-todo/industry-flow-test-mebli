---
skill: flow-research:past-projects-analyzer
date: 2026-11-10
status: open
kind: gap
fix: unknown
rule: "коли людина просить узяти для A-04 також Google Docs і дані робочої бази Odoo"
confidence: medium
evidence: ["запит людини в чаті 2026-11-10: перевірити Odoo читанням, Google Docs і AIKB", "SKILL.md: джерела — лише AIKB, Fathom, код; бази клієнтів не відкриваються; CLAUDE.md тесту: odoo_* заборонено"]
repeat_of: null
siblings_checked: ["flow-research:concept-mapper: ?"]
source: "tests/reports/A-04-2.md (тест mebli, етап 1)"
summary: Людина очікує Drive і Odoo як джерела досвіду, скіл їх не передбачає — відкрите питання до власника пакета
---
**Очікували (людина):** A-04 бере досвід також із Google Docs (звіти, ТР поза AIKB) і з нашої бази Odoo (що вже налаштовано).
**Отримали:** скіл має лише AIKB/Fathom/код; Drive і Odoo не читались (Odoo заборонено тестовим режимом, Drive — поза контрактом скіла, явного рішення людини не було).
**Пропозиція:** власнику flow-research вирішити: (а) Drive — через AIKB (індексувати документи туди) чи окреме джерело з колонкою `drive_file_id` у sources.md і режимом «лише звіти»; (б) Odoo — лише демо/тестові бази пакета з allow-list `odoo_connections`, ніколи прод клієнта. До рішення — не читати.
**Принцип:** —
