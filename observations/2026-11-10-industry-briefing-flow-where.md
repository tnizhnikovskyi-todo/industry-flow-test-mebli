---
skill: odoo19-discovery-initiation:industry-briefing
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли скіл запускається як крок флоу A-03 за нарядом з where і без компанії-замовника"
confidence: high
evidence: ["SKILL.md: «Збережи у папку outputs як галузь_[назва_галузі]_[назва_компанії].md», чек-лист Кроку 6 вимагає «реальну назву компанії»", "tests/naryad/A-03.yaml: where = docs/industries/mebli/briefing.md, компанії немає", "SKILL.md посилається на mcp__workspace__web_fetch, present_files, Claude in Chrome — у сесії флоу їх немає"]
repeat_of: null
siblings_checked: ["odoo19-discovery-initiation:competitor-mapper: ?", "odoo19-discovery-initiation:client-web-researcher: ?"]
source: "tests/reports/A-03.md (тест mebli, етап 1)"
summary: Скіл не знає where наряду і режиму «галузь без компанії»; шлях outputs/ і назва файлу з компанією не підходять для A-03
---
**Очікували:** режим «пакет/галузь» — результат за `where` наряду, без назви компанії, без інтерактивних кроків («запитай…», `present_files`, критик-раунд «за згодою BA»).
**Отримали:** скіл пише лише в `outputs/галузь_*_[компанія].md`; у тесті runner записав прямо в `where`, пункт чек-листа про назву файлу пропущено; WebFetch замість `mcp__workspace__web_fetch`.
**Пропозиція:** розділ «Наряд флоу» в SKILL.md: якщо є `where` — писати туди, ім'я файлу не міняти, назву компанії не вимагати; інструменти — через загальні WebSearch/WebFetch; кроки з людиною (уточнення, критик-раунд) пропускати й називати в memo.
**Принцип:** скіл, що є кроком флоу, бере шлях результату з наряду, а не з власної конвенції.
