# concept-presentation 0.2.0 — check_owner_page --sample перевіряє всі *.html теки; логотип

- Скіл: `flow-research:concept-presentation@0.2.0`; крок A-20c (зразок), 2026-11-12, тестове репо `mebli`
- Тип: прогалина скрипта / інструкції

1. `check_owner_page.py --sample` перевіряє всі `*.html` у `owner-page/`. При повторному запуску (recalc) старі `competitors.html`/`rejected.html` попереднього флоу дають FAIL `OP-contract`, хоча зразок — лише `index.html`. Довелося перевіряти копію теки з одним файлом. Пропозиція: у `--sample` перевіряти лише `index.html`.
2. Скіл вимагає логотип «у data:-URI (зменшений)», але виконавець без Bash не може згенерувати base64, а в `brand-todo/` немає зменшеної версії (оригінал 2277×891, 49 KB). Пропозиція: додати `todo-logo-240.png` (≈10 KB) або готовий `todo-logo.b64.txt` у бренд-кіт.
3. Виконавець профілю content не може отримати URL Artifact, а START-HERE вимагає погодити публікацію з власником — зразок лишається `waiting_human` без URL; варто описати цей шлях у `publish.md`.
