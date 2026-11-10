---
skill: odoo19-discovery-initiation:industry-briefing
date: 2026-11-10
status: open
kind: gap
fix: text
rule: "коли briefing.md є входом concept-mapper (A-20), що бере ролі зі «структури відділів у briefing»"
confidence: high
evidence: ["concept-mapper/SKILL.md, Крок 2: «Ролі … лише з джерел: структура відділів у briefing»", "шаблон Кроку 5 industry-briefing розділу структури відділів не має; TEST-START.md називає це очікуваною розбіжністю", "docs/industries/mebli/briefing.md: ролі названо лише в болях (конструктор, технолог, комірник …)"]
repeat_of: null
siblings_checked: ["flow-research:concept-mapper: same", "odoo19-discovery-initiation:competitor-mapper: ?"]
source: "tests/reports/A-03.md (тест mebli, етап 1)"
summary: Формат briefing не має «Структури відділів», яку A-20 використовує як джерело ролей
---
**Очікували:** у briefing.md розділ з типовими підрозділами й ролями галузі, на який A-20 може посилатися `briefing.md§<заголовок>`.
**Отримали:** розділу немає (формат 0.10.0/0.12.1); ролі є лише як підписи болів. A-20 або візьме ролі з болів (не передбачено його Кроком 2), або зупиниться на «ролей менше 4».
**Пропозиція:** узгодити формати сусідів: або додати в шаблон industry-briefing розділ «Типова структура відділів і ролі» (у режимі пакета), або в concept-mapper дозволити ролі з підписів болів briefing. Рішення — власникам обох скілів.
**Принцип:** формат результату кроку визначає вхід наступного — зміни погоджуються парою.
