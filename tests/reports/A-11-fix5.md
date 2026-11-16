# Звіт кроку A-11 (fix5: обмін з BAS/BAF відкладено зі збірки) — тестовий режим

Наряд: `tests/naryad/A-11-fix5.yaml` (`params.mode: fix`). Гілка `flow/A-11-fix5-test` від `origin/flow/A-17-6-test` @ `f48d954`.
Підстава — рішення власника 2026-11-16 «Приберіть зі збірки поки все, що пов'язано з BAS» (`flow/decisions.md` рядок 53; рядок вносила головна сесія, у цій гілці файл не змінювався).
Скіл `odoo19-mvp-build:code-dev` у сесії недоступний (скіл організації) — зміни зробила сесія. Тести — окрема доставка `/home/user/odoo19/delivery-bas`
(конфіги `odoo-tools-bas{,-light,-B}.conf`, порти 8197–8199), бази `test-mebli-bas-a148-*` (видалено); прогін — на вершині A-13-5, `package/addons` той самий, що в цій гілці (diff 0).

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix5, started: 2026-11-16T10:00:00Z, finished: 2026-11-16T10:55:00Z}
result: done
pr: "PR не створено (наказ сесії: PR робить головна сесія); гілка flow/A-11-fix5-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 250000, tokens_out: 30000, agent_hours: 0.9}   # оцінка
cost_estimated: true
base_sha: f48d954
checks:
  - {id: deferred-move, status: PASS, msg: "git mv: package/addons/td_mebli_bas -> package/deferred/td_mebli_bas; td_mebli_attendance (єдина функція — «Табель для BAS») -> package/deferred/td_mebli_attendance; td_mebli_migration/scripts/convert_bas.py + його тест -> package/deferred/td_mebli_migration/; package/deferred/README.md («відкладено рішенням власника 2026-11-16», порядок для існуючих баз, повернення)"}
  - {id: deps, status: PASS, msg: "скрипт-grep збірки: depends на td_mebli_bas/td_mebli_attendance — 0 (td_mebli_demo: -> hr_attendance); моделі/поля td.mebli.bas.*, td_bas_* у package/addons — 0; виклики convert_bas — 0"}
  - {id: demo, status: PASS, msg: "td_mebli_demo 19.0.1.1.5: прибрано _bas_exchange, _bas_codes (канал BAS, коди BAS, статуси обміну); rnd не зачеплено"}
  - {id: migration-steps, status: PASS, msg: "td_mebli_migration 19.0.1.1.7: кроки 26–28 «Коди BAS …» і примітка кроку 2 прибрано з даних (noupdate) і міграцією post-migrate 19.0.1.1.7 (unlink + note NULL); старі міграції 1.1.1/1.1.3 не пишуть примітку BAS; тести: 25 кроків, test_ac_089_no_steps_of_deferred_modules; .pot/uk.po — 5 записів прибрано, підказка module_name без td_mebli_bas"}
  - {id: install-helper, status: PASS, msg: "td_mebli_install 19.0.1.1.7: _td_cancel_pay_marks лишено як службовий (кличе лише відкладений AC-042), коментарі/підказка «cancelled» без обміну BAS (+ uk.po); тест перейменовано test_ac_021_cancel_marks_helper"}
  - {id: other, status: PASS, msg: "td_mebli_ua 1.1.4 (опис), td_mebli_cutting 1.1.4 (коментар), td_mebli_sale 1.1.4 (історична міграція 1.1.0 — позначка «відкладено»); AC-COVERAGE.md: банер + AC-039…042, 078, 109 — «відкладено»"}
  - {id: tests-clean, status: PASS, msg: "чисті бази (A-14-8): A — td_mebli_* 328/0 (skipped 1), td_knowledge+mebli 18/0, td_support 15/0, td_home_menu 6/0; light — 328/0, 18/0, 15/0, 6/0; B — 333/0, 18/0, 15/0, 6/0 (прогін 4 A-14-8, з тестом D-23). Було (A-14-7): 349/333/354 — мінус 22 тести відкладених модулів і converter-тесту, плюс 1 тест D-23"}
  - {id: d23-tech-rights, status: PASS, msg: "додаткове завдання (аудит setup.md, GAPS А): td_mebli_mrp 19.0.1.1.6 — рішення власника 2026-11-16 (права технолога; `flow/decisions.md` рядок 54): ACL group_technologist read/write/create без unlink на product.template/product, рядки й значення атрибутів шаблону, mrp.bom(+line), mrp.routing.workcenter, mrp.workcenter(+capacity); технічно + resource.resource (AI-39); D-23; тест test_d23_technologist_prepares_products_and_specifications — PASS (окрема база test-mebli-bas-d23, 5/0), у повному прогоні — A-14-8"}
  - {id: erratum, status: PASS, msg: "звіт виправлено в гілці A-16-7 (коміт звітів): числа тестів, посилання на flow/decisions.md рядок 54; код цієї гілки не змінювався"}
  - {id: lint, status: PASS, msg: "ruff змінених .py: нових знахідок 0 (test_migration 18 -> 15; full.py — давні B023/I001/F841/RUF059); новий migrations/19.0.1.1.7 — 0"}
  - {id: versions, status: PASS, msg: "+1 патч: demo 1.1.5, migration 1.1.7, install 1.1.7, ua 1.1.4, cutting 1.1.4, sale 1.1.4, mrp 1.1.6"}
  - {id: where-only, status: PASS, msg: "package/addons/{td_mebli_demo,_migration,_install,_ua,_cutting,_sale,_mrp}, AC-COVERAGE.md, перенесені td_mebli_bas/_attendance, package/deferred/, AI-DECISIONS (AI-37…AI-39), наряд, звіт; where наряду розширено проти A-11-fix4 на ці модулі"}
data_sources: ["repo:package/@f48d954", "/home/user/odoo19/src (Odoo 19.0 CE)", "local:test-mebli-bas-a148-{A,light,B,cv} (видалено)"]
memo: |
  Рішення AI (власник — вето): AI-39 (технічні доповнення до рішення власника 2026-11-16 про права технолога: resource.resource; «Виключити для» і видалення — адміністратор); AI-37 (що відкладено і як: модулі цілком у package/deferred/, хелпер AC-042 лишився), AI-38 (існуючі бази:
  спершу штатно видалити td_mebli_bas і td_mebli_attendance, поки код у addons_path; окремої міграції з SQL-чисткою немає — поля належать
  відкладеним модулям). Невпевнений: (1) світлий профіль тепер за модулями = A (різниця лише параметри SPEC §11.3); (2) оновлення бази, де модулі
  вже стояли, не перевірено (бази клієнтів немає) — ризик AI-38; (3) td_mebli_base: коментар групи «Фінансист» («exchange with the accounting»)
  не змінено — це не функція. Відкладений код не тестується CI.
  Недовірені дані: інструкцій не виявлено. Odoo-mcp не використовувався.
observations: []
```
