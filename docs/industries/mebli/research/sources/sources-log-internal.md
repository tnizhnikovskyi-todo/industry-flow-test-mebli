# sources-log — група 1 (внутрішні дані ToDo), 2026-11-11
Підстава: рішення власника в сесії 2026-11-11 — дозволено всі доступні дані ToDo, лише читання. Клієнти у висновках — коди K-NN.

| Що | Звідки | Дата доступу | Клас даних |
|---|---|---|---|
| crm.lead: меблеві ліди/угоди 2023–2026 (назва, стадія, причина програшу, опис), 140 записів, 56 проаналізовано | odoo-mcp, `o18-artel-prod` (connection `default`), `odoo_search_read` | 2026-11-11 | commercial; personal (контакти в описах — не перенесено) |
| crm.lead: холодні дзвінки кампанії AI-менеджера (агрегат, 25) | там само | 2026-11-11 | commercial |
| crm.lost.reason (довідник) | там само | 2026-11-11 | commercial |
| project.task: пресейл-задачі меблевих клієнтів (9 описів) | там само | 2026-11-11 | commercial |
| project.project, helpdesk.ticket (пошук, 0–1 збіг) | там само | 2026-11-11 | commercial |
| Fathom: зустріч 196163757 (2026-10-26), 180841339 (2026-09-08) — **AI-підсумки** Fathom (не дослівно; повні транскрипти не брались) | Fathom `search_meetings`, `get_meeting_summary` | 2026-11-11 | commercial; personal (імена — не перенесено) |
| Unitalk: list_transcriptions «мебл», «розкр», «кухн» (безкоштовно) | Unitalk Transcribe | 2026-11-11 | personal (номери — не перенесено); commercial |
| Unitalk call_dbid 37392 (дзвінок 2026-09-18) — повний транскрипт через get_transcription; використано в рядках 50–51 | Unitalk Transcribe | 2026-11-11 | personal (не перенесено); commercial |
| Unitalk call_dbid 38032, 41465 — get_transcription; не меблеві, не використано | Unitalk Transcribe | 2026-11-11 | personal; commercial |
| Unitalk call_dbid 41032 (2026-10-22), 42054 (2026-10-29), 43297 (2026-11-10) — **лише AI-підсумок зі списку** list_transcriptions, транскрипт не відкривався; рядки 74–75 | Unitalk Transcribe | 2026-11-11 | commercial |
| AIKB: list_projects; пошук у `1-проекти-на-передпродажу`, `2-архів`, два проєкти дизайн-студій; find_documents «мебл», «furnit» | AIKB | 2026-11-11 | commercial |
| AIKB, K-29: звіт про обстеження, drive_file_id `1zX42fZEw-5ud6JEMhhr_Ni66qDo_HOri` (рядки 66, 68); номенклатура комплектації, drive_file_id `1tZuKOvzf77E3r1gt4pQ3JSzhGSlN-mp0` (рядок 67). Дата документа в AIKB не вказана (`modified_at` = null) | AIKB `find_documents` | 2026-11-11 | commercial |
| AIKB `2-архів`: табель обліку часу проєкту ToDo, drive_file_id `1RiPZyezdoSvYDpFkTzcN4YXTnBb1Qcu78ou4eFoY2uo`, записи 2024-01-29, 2024-02-02, 2024-02-25 (рядок 69) | AIKB `search_knowledge_base` | 2026-11-11 | commercial; personal (ПІБ виконавців — не перенесено) |
| Gmail: search_threads «меблі/кухні/furniture» за 2 роки (11 тредів), підсумки Fathom (5); get_thread 19f6fdba268addc6, 1a17776223374546 | Gmail (лише читання) | 2026-11-11 | commercial; personal (адреси — не перенесено) |
| factory3d: CONSISTENCY.md, розділи «Питання до замовника» і «Відповіді» (рядки 191–262, grep) | `/home/user/todo_timur/factory3d/docs/CONSISTENCY.md` | 2026-11-11 | commercial (внутрішній проєкт) |
| FUNCTIONAL-MAP.md — лише читання ID (grep) | `docs/industries/mebli/research/FUNCTIONAL-MAP.md` | 2026-11-11 | none |
| Доопрацювання за рецензією: звірка цитат crm.lead#23058, #25819 (поле description) | odoo-mcp, `o18-artel-prod` (connection `default`), `odoo_search_read` | 2026-11-11 | commercial; посилання на Drive — не відкривались |
