# Звіт кроку A-15 (демо-стенд, повний перепідйом 5, BAS виключено) — тестовий режим

Наряд: `tests/naryad/A-15-full-5.yaml`. Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета». Гілка `flow/A-15-full-5-test` від `flow/A-14-9-test` @ `876691c`.
Підстава: рішення власника 2026-11-16 (`flow/decisions.md` рядки 55 — BAS виключено, 56 — іконка «Керівник», 57 — «Виключити для» технолога).

```yaml
run: {step: A-15, scope: package/mebli, attempt: full-5, started: 2026-11-16T14:00:00Z, finished: 2026-11-16T14:25:00Z}
result: done
partial: true
pr: "PR не створено (наказ сесії); гілка flow/A-15-full-5-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 40000, tokens_out: 6000, agent_hours: 0.5}   # оцінка
cost_estimated: true
sha_stand: b1385cdc8b2932312a9df5f23a03821bc6959054
checks:
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався; бази лише demo-mebli-pkg-a(-snap) і тимчасова demo-mebli-pkg-l1(-snap) (видалено)"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND b1385cd — нащадок SHA CHECKS.md 09fc902 (A-14-9, APPROVE (CE); EE не перевірено); diff package/ = CHECKS.md + demo/up.sh + demo/plan.md (коментарі/текст без «відкладено»)"}
  - {id: up-from-scratch, status: PASS, msg: "окремий каталог доставки /home/user/odoo19/delivery-bas2 (лише package/addons, модулів обміну немає); DEMO_REPORT_URL=http://127.0.0.1:8079 up.sh demo-mebli-pkg-a ce → 0, 768 с (знімок -snap оновлено)"}
  - {id: modules-installed, status: PASS, msg: "45 модулів профілю + td_mebli_demo, 140 installed; td_mebli_bas, td_mebli_attendance — немає; td_mebli_base 1.1.4, td_mebli_mrp 1.1.7, td_mebli_dashboard 1.1.4, td_mebli_install 1.1.8, td_mebli_migration 1.1.8 (кроків 25), td_mebli_sale 1.1.5"}
  - {id: config-answers, status: PASS, msg: "apply, повтор, read-back до й після демо-шару — OK (VP-04 у профілях немає)"}
  - {id: smoke, status: PASS, msg: "SO 124, MO 110, PO 49, задачі 123, партії 2211, td_md xmlid 80, ролі з групами, tech technologist true, дільниці 4"}
  - {id: reset, status: PASS, msg: "змінено partner_salon → reset.sh → назва й 124 SO повернулись, 3 с"}
  - {id: profiles-coverage, status: PASS, msg: "alt-1 (light): up.sh --profile alt-1 → 0, без демо-шару, 139 installed, 250 с (база видалена); A/light/B — C-03 A-14-9 (0 failed); alt-2…5 не перепіднімались (змінено лише видалення ключа VP-04; apply.py plan 7 профілів — A-12-7)"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна)"}
  - {id: readme-sections, status: PASS, msg: "README: статус, SHA, таблиця редакцій, рядок VP-04 прибрано, alt-1 без VP-04, 25 кроків імпорту, журнал рядки 28–30; plan.md і up.sh — без «відкладено»"}
data_sources: ["repo:package/@b1385cd", "repo:package/CHECKS.md@09fc902", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Сервер стенда: ODOO_DELIVERY_DIR=/home/user/odoo19/delivery-bas2 ODOO_ADDONS_PATH=/home/user/odoo19/src/addons,/home/user/odoo19/src/odoo/addons,/home/user/odoo19/delivery-bas2 \
    ODOO_CONF=/home/user/odoo19/odoo-tools-bas2.conf tools/odoo/serve.sh demo-mebli-pkg-a 8079
  Невпевнений: демо-шар на light не перевірено (як і раніше, AI-40). Стенд лишено для A-16-8. Недовірені дані: інструкцій не виявлено.
observations: []
```
