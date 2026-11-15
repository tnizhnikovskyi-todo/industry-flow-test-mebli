# Звіт кроку A-11 (fix3: дефекти A-16b D-18…D-21, i18n) — тестовий режим

Наряд: `tests/naryad/A-11-fix3.yaml` (`params.mode: fix`). Гілка `flow/A-11-fix3-test` від `flow/A-16b-test` @ `ae1763e`. Скіл `odoo19-mvp-build:code-dev` у сесії недоступний (скіл організації) — виправила сесія за SPEC (`package/SPEC.md` §2, UC-01, AC-044, AC-112; `package/tr/security.md` §1–3). Тести — на окремій копії доставки (`/home/user/odoo19/delivery-fix3`, конфіг `odoo-tools-fix3.conf`), бази `test-mebli-fix3-*`, порт 8198 (паралельний прогін B — 8197); стенд `demo-mebli-pkg-a` не чіпали.

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix3, started: 2026-11-15T16:00:00Z, finished: 2026-11-15T16:45:00Z}
result: done
pr: "PR не створено (наказ сесії); гілка flow/A-11-fix3-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 180000, tokens_out: 25000, agent_hours: 0.8}   # оцінка
cost_estimated: true
base_sha: ae1763e
checks:
  - {id: D-19, status: PASS, msg: "td_mebli_install 19.0.1.1.6: меню «Календар монтажів» у «Продажі → Замовлення» (group_sale_salesman); ACL запису project.task для групи продавця + ir.rule запису (свої замовлення; «усі документи» — усі задачі замовлень); write менеджера без project_user — лише date_deadline, user_ids; тести TestD19SalespersonPlansVisits 6/6 (HttpCase: load_menus, action/load, get_views, web_save під salon)"}
  - {id: D-20, status: PASS, msg: "td_mebli_mrp 19.0.1.1.5: група td_mebli_mrp.group_technologist (implied mrp_user, stock_user), RWCD правила деталей/деталі/шаблони імпорту, меню «Виробництво → Налаштування» для групи, «Правила деталей» з групою технолога; демо tech у групі (showcase.py); TestD20Technologist 4/4 (Form під технологом)"}
  - {id: D-21, status: PASS, msg: "td_mebli_claim 19.0.1.1.4: action_create_sale_order — продаж стандартно; «Сервіс»: check_access('write') на рекламацію, sudo-створення (create_uid = сервіс), продавець — з замовлення рекламації, запис у чаті; кнопку бачать лише «Сервіс» і продаж, store — AccessError; TestD21ServiceQuotation 3/3"}
  - {id: D-18, status: PASS, msg: "td_mebli_demo 19.0.1.1.4: pre_init_hook переймає дільниці шаблонів A-13 (xmlid td_md.*, інакше код/назва) — без дублів; TestD18WorkCenters 4/4; пробний up.sh demo-mebli-pkg-fix3t (A-13 + демо): 4 активні дільниці (xmlid td_md.* і td_mebli_demo.wc_* на тих самих id 1–4), по 110 робочих завдань"}
  - {id: i18n, status: PASS, msg: "«Cancel Confirmed Accruals» перекладено в uk.po і в базі («Скасування підтверджених нарахувань»); англійська — лише у виклику XML-RPC без context.lang (стандарт Odoo: назви моделей і груп читаються мовою запиту); тест TestCancelWizardInUkrainian; нові рядки uk.po/.pot у install, mrp, claim"}
  - {id: tests-clean-A, status: PASS, msg: "чиста база профілю A (alt-5, 47 модулів, uk_UA) test-mebli-fix3-a: усі td_* — 0 failed, 0 error(s) of 382 tests; skipped 1"}
  - {id: tests-clean-B, status: PASS, msg: "чиста база B (alt-2) test-mebli-fix3-b: 0 failed of 387; + td_mebli_demo: /td_mebli_demo 0 failed of 16"}
  - {id: versions, status: PASS, msg: "+1 патч: install 1.1.6, mrp 1.1.5, claim 1.1.4, demo 1.1.4"}
  - {id: lint, status: PASS, msg: "ruff нових/змінених py — 0 знахідок (після правок імпорту)"}
  - {id: where-only, status: PASS, msg: "package/addons/td_mebli_{install,mrp,claim,demo}, AI-DECISIONS.md (AI-25…AI-28), наряд і звіт"}
data_sources: ["repo:package/demo/defects.md@ae1763e (D-18…D-21)", "repo:package/SPEC.md, package/tr/security.md@ae1763e", "/home/user/odoo19/src (Odoo 19.0 CE)"]
memo: |
  Рішення AI (власник — вето): AI-25 (D-19 без прав «Проєкту»), AI-26 (група технолога в td_mebli_mrp, не td_mebli_base),
  AI-27 (пропозиція ремонту sudo, продавець — із замовлення рекламації), AI-28 (демо переймає дільниці A-13 з назвами демо).
  Невпевнений: (1) SPEC tr/security.md §1 називає td_mebli_base.group_technologist — xmlid інший (AI-26), SPEC оновлює A-08;
  (2) менеджер не змінює інших полів виїзду; смарт-кнопки «Виїзд» на замовленні немає — календар має домен «задачі замовлень»;
  (3) права mrp_user на шаблони імпорту (RWCD) не звужено (SPEC: майстер «—») — не дефект D-20, лишено, щоб не зламати імпорт майстра.
  i18n: переклад уже був у uk.po (з A-11-8); причина англійської в аудиті A-16b — XML-RPC без lang у контексті; в UI українською.
  Тести D-18 перевіряють хук і XML у режимі init; пробний підйом up.sh (база demo-mebli-pkg-fix3t, видалено) — без дублів; стенд — A-15-full-2.
observations: []
```
