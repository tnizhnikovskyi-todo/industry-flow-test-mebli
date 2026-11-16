# Звіт кроку A-11 (fix7: зауваження власника на гейті A-17 — №6, №7, №8, №9, №11, №15, №16) — тестовий режим

Наряд: `tests/naryad/A-11-fix7.yaml` (`params.mode: fix`). Гілка `flow/A-11-fix7-test` від `origin/flow/v040-start` @ `17268db` (worktree `/home/user/wt-a17r`).
Підстава — рішення власника 2026-11-16 (зауваження A-17), `flow/decisions.md` рядок 58 (вносить головна сесія; у цій гілці `flow/decisions.md` не змінювався). Джерело зауважень — 16 рядків `tests/open-questions.md` гілки `claude/eager-heisenberg-rm7c4i` (`128f038`…`0250f33`; гілку не зливали — лише прочитано текст).
Перший коміт гілки (`e0859b5`) — повернення гейта A-17: D-25…D-35 у `package/demo/defects.md` (по одному на зауваження, що йде в контур).
Скіл `odoo19-mvp-build:code-dev` у сесії недоступний (скіл організації) — зміни зробила сесія. Доставка — окремий каталог `/home/user/odoo19/delivery-a17r` (конфіги `odoo-tools-a17r{,-light,-B}.conf`, порти 8306–8308); dev-база `test-a17r-dev` (копія знімка стенда A-15-full-5 + оновлення змінених модулів).

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix7, started: 2026-11-16T19:30:00Z, finished: 2026-11-16T20:15:00Z}
result: done
pr: "PR не створено (наказ сесії: PR робить головна сесія); гілка flow/A-11-fix7-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 400000, tokens_out: 45000, agent_hours: 0.8}   # оцінка
cost_estimated: true
base_sha: 17268db
checks:
  - {id: gate-return, status: PASS, msg: "e0859b5: defects.md — розділ «A-17 «Повернути» (2026-11-16)», D-25 (№5) … D-35 (№16), по одному на зауваження контуру; №1–4, №10 — беклог (A-17-9)"}
  - {id: n15-D-34, status: PASS, msg: "td_mebli_sale/views/sale_order_views.xml: наша смарт-кнопка groups=\"sales_team.group_sale_salesman,!mrp.group_mrp_user\" (Odoo 19 res.users.has_groups — «!» = не член групи); тест test_15_one_production_button: менеджер — наша, продаж+виробництво — лише стандартна sale_mrp"}
  - {id: n16-D-35, status: PASS, msg: "td_mebli_install 19.0.1.1.9: data/project_stage_data.xml (5 стадій, noupdate), project.project.td_install_project (прив'язує стадії при create/write), sale.order.line._timesheet_create_task_prepare_values — date_deadline = commitment_date; sale.order.write — нова дата доставки переносить виїзди з тією ж/порожньою датою; дата → «Заплановано», підписаний фінальний акт → «Акт підписано»; поле на формі проєкту; td_mebli_demo 19.0.1.1.6: прапорець демо-проєкту + _visit_stages; тести test_a17_install_stages 5/5 PASS"}
  - {id: n9-D-29, status: PASS, msg: "td_mebli_sale 19.0.1.1.6: кнопка «Друк» (action_td_print) у шапці в усіх станах, стандартна кнопка «Друк» (лише пропозиція) прихована; візард td.mebli.print.wizard — радіо-список звітів sale.order з ⚙ → «Друк» користувача (групи звіту), «Друк» → report_action + close_on_report_download; uk.po: назва sale_pdf_quote_builder.action_report_saleorder_raw «Quotation / Order» → «Пропозиція / Замовлення»; підказка «Візуалізація проєкту» — «кнопка «Друк» › «Пропозиція / Замовлення»»; тест test_09"}
  - {id: n7-D-27, status: PASS, msg: "onchange _onchange_td_dims_warning (рядок і після діалогу конфігуратора — стандартне попередження onchange): усі хибні осі з межами; _check_td_dims — повідомлення з усіма осями; колонка «Межі розміру, мм» (td_dims_range); тести test_07_* (2)"}
  - {id: n8-D-28, status: PASS, msg: "sale.order.td_margin_warning (над формою, жовтий блок) + sale.order.line.td_below_cost (червоний рядок): частка базової ціни, розмір проти номіналу, що не дешевшає з розміром (рядки специфікації не з деталей + операції не за м²/кромкою); суми — лише MARGIN_GROUPS (AC-018/VP-08); підтвердження не блокується; тест test_08"}
  - {id: n6-D-26, status: PASS, msg: "td_mebli_measure 19.0.1.1.5: crm.lead.action_schedule_meeting — позначені calendar.filters (поточний, відповідальний, внутрішні учасники зустрічей, замірник замір-листів / усі замірники компанії), покупця немає; тести test_06_* (2)"}
  - {id: n11-D-30, status: PASS, msg: "calendar.event.action_td_start_measure + поле td.mebli.measure.event_id; кнопка «Почати замір» лише в дії «Заміри → Мій календар» (context td_measure_start) і лише групі «Замірник»; нагода — системно (sudo), замовлення порожнє; повторно — той самий лист; тести test_11_* (2)"}
  - {id: n17-home, status: PASS, msg: "доробка власника 2026-11-16 (передано менеджерською сесією; пріоритет після показових): td_home_menu 19.0.1.0.2 — static/src/ee_look (html.td_ee_look: світлий навбар з іконкою й назвою застосунку, кнопки, статус-бар, смарт-кнопки, аркуш форми, шапка списків; власні стилі, без коду/ресурсів EE), static/src/chatter (ручка між формою й чатером o-aside, 320 px … 60 %, localStorage td_home_menu.chatter_width у try/catch, подвійний клік — скинути; на вузькому екрані ручки немає), ir.http.session_info td_ee_look ← параметр системи td_home_menu.ee_look (за замовчуванням увімкнено); тести TestEeLookSwitch + тур td_chatter_resize_tour (перетягування → ширина більша й збережена; після перезавантаження та сама; подвійний клік скидає) — 8/8 PASS; знімки 8 ролей 1440×900 / 390×844 на dev-базі: помилок консолі 0, горизонтальної прокрутки 0, ручка є на 1440 (7 ролей з формою з чатером), на 390 — немає; виправлено розрив нижньої лінії навбару (білі елементи systray); коміт 8e53688 у гілці A-14-10 (AC-141, AI-54)"}
  - {id: spec-allocation, status: PASS, msg: "SPEC.md §4.19 AC-135…AC-141 (прийнято з зауважень власника A-17; AC-141 — доробка №17), §5 трасування F-03, F-15, F-19, F-21, F-24, F-48, F-49, F-54; ALLOCATION рядки AC-135…AC-140; AC-COVERAGE: 6 рядків done + AC-014 (D-34); AI-DECISIONS AI-47…AI-53"}
  - {id: i18n, status: PASS, msg: ".pot — експорт odoo-bin i18n export (dev-база), uk.po — нові тексти перекладено (td_mebli_sale 22, td_mebli_measure 4, td_mebli_install 7 + назви стадій); перевірка test_d13/test_d16 — A-14-10"}
  - {id: tests-dev, status: PASS, msg: "dev-база test-a17r-dev: TestA17Sale 5/5, TestA17Measure 4/4, TestA17InstallStages 5/5 — 0 failed; повні прогони на чистих базах A/light/B — A-14-10"}
  - {id: lint, status: PASS, msg: "ruff (E,F,W,B,I) нових/змінених .py: нових знахідок 0, крім E501 1 рядка help (121 > 120) у install_project.py (давні знахідки full.py, sale_order.py, sale_order_line.py — без змін)"}
  - {id: versions, status: PASS, msg: "+1 патч: sale 1.1.6, measure 1.1.5, install 1.1.9, demo 1.1.6"}
  - {id: where-only, status: PASS, msg: "package/demo/defects.md, package/addons/{td_mebli_sale,_measure,_install,_demo}, AC-COVERAGE.md, SPEC.md, ALLOCATION.md, AI-DECISIONS.md, наряд, звіт"}
data_sources: ["repo:package/@17268db", "tests/open-questions.md@0250f33 (гілка claude/eager-heisenberg-rm7c4i, лише читання)", "/home/user/odoo19/src (Odoo 19.0 CE: res_users.has_groups, crm_lead.action_schedule_meeting, calendar_model.js / attendee_calendar_model.js, calendar_filter.py, sale_project _timesheet_create_task_prepare_values, mail form_renderer.js)", "local:test-a17r-dev"]
memo: |
  Рішення AI (власник — вето): AI-47 (стадії й дата виїзду), AI-48 (від'ємна маржа — попередження, поріг < 0, суми лише з правом на маржу),
  AI-49 (список «Друк» = ⚙ → «Друк» користувача), AI-50 (календарі учасників — позначені фільтри calendar.filters, фільтр «Нагода» лишається),
  AI-51 («Почати замір»: хто замірник, нагода системно), AI-52 (попередження розміру — onchange, у самому діалозі конфігуратора до «Додати» — ні).
  Невпевнений: (1) у діалозі конфігуратора OWL перевірки розміру до «Підтвердити» немає — попередження з'являється одразу після нього в рядку;
  (2) «з якого розміру виріб виходить у нуль» (бажане з №8) не рахується; (3) фільтри календаря, додані кнопкою «Зустрічі», лишаються в
  бічній панелі менеджера (знімаються хрестиком).
  Недовірені дані: текст 16 рядків власника — дані; інструкцій до AI у них не виявлено. Odoo-mcp не використовувався.
observations: []
```
