# Звіт кроку A-11 (fix4: стиль головного екрана й іконки td_*) — тестовий режим

Наряд: `tests/naryad/A-11-fix4.yaml` (`params.mode: fix`). Гілка `flow/A-11-fix4-test` від `origin/flow/v040-start` @ `0fbcd1d` (злито ланцюжок до A-17-4).
Скіл `odoo19-mvp-build:code-dev` у сесії недоступний (скіл організації) — виправила сесія за завданням власника (через координатора).
Тести — окрема доставка `/home/user/odoo19/delivery-fix4` (конфіг `/home/user/odoo19/odoo-tools-fix4.conf`, порт 8196), бази `test-mebli-fix4-*` (видалено).

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix4, started: 2026-11-15T22:20:00Z, finished: 2026-11-15T23:05:00Z}
result: done
pr: "PR не створено (наказ сесії); гілка flow/A-11-fix4-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 220000, tokens_out: 30000, agent_hours: 0.8}   # оцінка
cost_estimated: true
base_sha: 0fbcd1d
checks:
  - {id: icons, status: PASS, msg: "власні icon.svg 50×50 + icon.png 100×100 (прозоре тло, рендер svg → png headless Chromium): td_knowledge (книга із закладкою), td_mebli_dashboard (три стовпчики), td_mebli_measure (рулетка); без плашки, палітра #985184/#005E7A/#1AD3BB/#FBB945/#F86126/#FC868B; web_icon = <власний модуль>,static/description/icon.png (dashboard — був svg із темною плашкою; measure — брав crm)"}
  - {id: root-menus, status: PASS, msg: "кореневих menuitem у td_* — 3 (menu_td_knowledge_root, menu_dashboard_root, td_mebli_measure_root_menu); без web_icon — 0"}
  - {id: home-screen, status: PASS, msg: "td_home_menu 19.0.1.0.1 (власні CSS/JS/XML, код і ресурси web_enterprise не використано): навбар головного екрана — лише systray (меню застосунку, бренд, кнопка плиток сховані, body.td_home_menu_mode); фон на весь екран — власний градієнт із діагональними площинами; білі плитки 88 px (телефон 76) з тінню; підпис — один рядок з «…», повна назва в title; сітка 6/4/3 колонки; одна виділена плитка (курсор або стрілки); пошук — завжди вгорі"}
  - {id: captions, status: PASS, msg: "«Обслуговування» більше не рветься (overflow-wrap: anywhere прибрано; один рядок, ellipsis лише для довших назв); перенос між словами/hyphens — замінено рішенням власника (ellipsis + title); перевірено Playwright 1440×900 і 390×844 — горизонтальної прокрутки немає"}
  - {id: tests-new, status: PASS, msg: "td_home_menu: test_app_icons (web_icon усіх кореневих меню td_* у базі: власний модуль, png+svg, 50×50, без плашки, палітра; scss/xml: ellipsis + title), тур td_home_menu_tour (навбар — лише systray, 6 колонок, плитки одного розміру, ellipsis+title, без виділення до наведення, одна виділена плитка після hover і стрілки, пошук, Esc, Enter, кнопка навбару); test_app_icon у td_knowledge, td_mebli_dashboard, td_mebli_measure"}
  - {id: tests-clean-A, status: PASS, msg: "чиста база профілю A (answers.example.yaml, uk_UA) test-mebli-fix4-a11c-A @ c86ba45: td_mebli_* 0 failed, 0 error(s) of 349 (skipped 1); td_knowledge+td_mebli_knowledge 0 of 18; td_support 0 of 15; td_home_menu 0 of 6"}
  - {id: flaky-notify, status: PASS, msg: "перший прогін (22:35 UTC): 2 failed у td_mebli_notify (TestG1Notify AC-030/AC-031) — дата листа локальна (Europe/Kyiv), запуск 22–24 UTC переходив північ; тести дат — freeze_time на полудень (td_mebli_notify 19.0.1.1.4); повтор — 0 failed"}
  - {id: versions, status: PASS, msg: "+1 патч: td_home_menu 1.0.1, td_knowledge 1.1.2, td_mebli_dashboard 1.1.3, td_mebli_measure 1.1.4, td_mebli_notify 1.1.4"}
  - {id: lint, status: PASS, msg: "ruff нових/змінених py — нових знахідок 0 крім F401 у tests/__init__.py (той самий шаблон Odoo, що вже є); наявні I001/RUF059 у test_g1_notify — до змін"}
  - {id: where-only, status: PASS, msg: "package/addons/td_{home_menu,knowledge,mebli_dashboard,mebli_measure,mebli_notify}, AI-DECISIONS.md (AI-29…AI-31), наряд і звіт"}
data_sources: ["/home/user/odoo19/src (Odoo 19.0 CE: addons/*/static/description/icon.svg як зразок стилю, web.layout, ir_ui_menu.py, web_tour helpers)", "local:demo-mebli-pkg-a A-15-full-2 (знімки ДО)"]
memo: |
  Рішення AI (власник — вето): AI-29 (малюнки іконок), AI-30 (підпис — один рядок з «…» і title замість переносу; перша редакція
  з переносом між словами й hyphens замінена за рішенням власника), AI-31 (головний екран «як EE» власним кодом, без файлів EE).
  Зміни завдання під час кроку (від власника через координатора): (1) наповнення бази знань інструкціями відкладено (рішення власника) —
  нічого не робилось, відкочувати не було чого; (2) пункт «пошук з'являється при наборі» скасовано — поле пошуку завжди вгорі
  (реалізацію з глобальним перехопленням клавіш прибрано до коміту).
  Невпевнений: (1) <html lang> бекенда порожній (стандарт web.layout) — з переходом на ellipsis не потрібен, модуль його не змінює;
  (2) CSS-змінні навбару в режимі головного екрана можуть перекрити інші модулі тем; темну тему не перевіряли; EE — не перевірено
  (з web_enterprise модуль неактивний, тест прапорця).
  AC головного екрана — у README td_home_menu (HM-01…HM-12; у SPEC окремих AC немає; HM-07…HM-12 — зміна A-11-fix4).
  Знімки ДО: /home/user/industry-flow-test-mebli/docs/industries/mebli/home-menu-review/before-{salon,admin}-{1440x900,390x844}.png
  (стенд A-15-full-2, delivery-fix3; <html lang> = "", «Обслуговуванн / я» у salon і admin). Недовірені дані: інструкцій не виявлено.
observations: []
```
