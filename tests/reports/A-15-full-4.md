# Звіт кроку A-15 (демо-стенд, повний перепідйом 4, BAS відкладено) — тестовий режим

Наряд: `tests/naryad/A-15-full-4.yaml`. Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета». Гілка `flow/A-15-full-4-test` від `flow/A-14-8-test`.
Підстава: рішення власника 2026-11-16 (`flow/decisions.md` рядок 53 — BAS поза збіркою; рядок 54 — права технолога).

```yaml
run: {step: A-15, scope: package/mebli, attempt: full-4, started: 2026-11-16T11:45:00Z, finished: 2026-11-16T12:15:00Z}
result: done
partial: true
pr: "PR не створено (наказ сесії); гілка flow/A-15-full-4-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 40000, tokens_out: 6000, agent_hours: 0.5}   # оцінка
cost_estimated: true
sha_stand: 63ca32947a1ec656e1484c728a4abb3504daf12c
checks:
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався; бази лише demo-mebli-pkg-a(-snap) і тимчасова demo-mebli-pkg-l1(-snap) (видалено); demo-mebli-full / -sample не чіпались"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND 63ca329 — нащадок SHA CHECKS.md e682ecb (A-14-8, APPROVE (CE); EE не перевірено); diff package/ = CHECKS.md + demo/up.sh"}
  - {id: up-script, status: PASS, msg: "up.sh: майстер-дані без --exclude кодів BAS (25 шаблонів), демо-шар — для коробок A/B (VP-01 ≠ light), раніше умова «є td_mebli_bas» (AI-40)"}
  - {id: up-from-scratch, status: PASS, msg: "окремий каталог доставки /home/user/odoo19/delivery-bas (конфіг odoo-tools-bas.conf), без td_mebli_bas/td_mebli_attendance; DEMO_REPORT_URL=http://127.0.0.1:8079 up.sh demo-mebli-pkg-a ce → 0, 781 с"}
  - {id: modules-installed, status: PASS, msg: "45 модулів профілю + td_mebli_demo, 140 installed (було 142); td_mebli_bas, td_mebli_attendance — немає; hr_attendance installed; td_mebli_mrp 1.1.6, td_mebli_demo 1.1.5, td_mebli_migration 1.1.7 (кроків 25)"}
  - {id: config-answers, status: PASS, msg: "apply, повтор, read-back до й після демо-шару — OK (VP-04 = false)"}
  - {id: smoke, status: PASS, msg: "SO 124, MO 110, PO 49, задачі 123, партії 2211, td_md xmlid 80, ролі з групами, tech technologist true"}
  - {id: reset, status: PASS, msg: "змінено partner_salon → reset.sh → назва й 124 SO повернулись, 3 с"}
  - {id: profiles-coverage, status: PASS, msg: "alt-1 (light): up.sh --profile alt-1 → 0, без демо-шару, 139 installed, 272 с (база видалена); A/light/B — C-03 A-14-8 (0 failed); alt-2…5 не перепіднімались (змінено лише VP-04 → false)"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна)"}
  - {id: readme-sections, status: PASS, msg: "README: статус, SHA, VP-04, журнал рядки 25–27; plan.md: UC-05 і light без BAS"}
data_sources: ["repo:package/@63ca329", "repo:package/CHECKS.md@e682ecb", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Сервер стенда: ODOO_DELIVERY_DIR=/home/user/odoo19/delivery-bas ODOO_ADDONS_PATH=/home/user/odoo19/src/addons,/home/user/odoo19/src/odoo/addons,/home/user/odoo19/delivery-bas \
    ODOO_CONF=/home/user/odoo19/odoo-tools-bas.conf tools/odoo/serve.sh demo-mebli-pkg-a 8079
  Рішення AI: AI-40 (умова демо-шару). Невпевнений: демо-шар на light не перевірено (як і раніше). Стенд лишено для A-16-7.
  Недовірені дані: інструкцій не виявлено.
observations: []
```
