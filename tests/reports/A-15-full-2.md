# Звіт кроку A-15 (демо-стенд, повний перепідйом, контур коду 2) — тестовий режим

Наряд: `tests/naryad/A-15-full-2.yaml` (не refresh). Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета», повний перепідйом після A-14-6. Гілка `flow/A-15-full-2-test` від `flow/A-14-6-test` @ `5bd4c57`.

```yaml
run: {step: A-15, scope: package/mebli, attempt: full-2, started: 2026-11-15T17:15:00Z, finished: 2026-11-15T17:40:00Z}
result: done
partial: true
pr: "PR не створено (наказ сесії); гілка flow/A-15-full-2-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 60000, tokens_out: 6000, agent_hours: 0.4}   # оцінка
cost_estimated: true
sha_stand: 15dbd6f7504fe49f174af6874f6ed99865365ea8
checks:
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався; бази лише demo-mebli-pkg-a(-snap) і пробна demo-mebli-pkg-fix3t (A-11-fix3, видалено); demo-mebli-full / -sample не чіпались"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND 15dbd6f — нащадок SHA CHECKS.md ba0aff3 (A-14-6, APPROVE (CE); EE не перевірено); diff package/ = CHECKS.md + data/verify_demo.py (лише перевірки smoke)"}
  - {id: up-from-scratch, status: PASS, msg: "DEMO_REPORT_URL=http://127.0.0.1:8079 up.sh demo-mebli-pkg-a ce → 0, 777 с, без ручних кроків"}
  - {id: modules-installed, status: PASS, msg: "47 модулів профілю + td_mebli_demo, 142 installed; td_mebli_install 1.1.6, mrp 1.1.5, claim 1.1.4, demo 1.1.4"}
  - {id: config-answers, status: PASS, msg: "apply, compare, read-back 23/23 до й після демо-шару"}
  - {id: smoke, status: PASS, msg: "SO 124, MO 110, PO 49, задачі 123, партії 2225, td_md xmlid 80, ролі з групами, tech technologist true, дільниці [Розкрій, Крайкування, Присадка, Складання], пробне замовлення ПДВ 20 %"}
  - {id: D-18, status: PASS, msg: "4 активні дільниці (ids 1–4), xmlid td_md.* і td_mebli_demo.wc_* на тих самих записах — дублів немає; defects.md D-18 — закрито"}
  - {id: reset, status: PASS, msg: "змінено partner_salon → reset.sh → назва й 124 SO повернулись, 2 с"}
  - {id: profiles-coverage, status: SKIP, msg: "alt-1…5 не перепіднімались: профілі й конфіг не змінено; регрес A/light/B — C-03 A-14-6 (0 failed)"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна)"}
  - {id: readme-sections, status: PASS, msg: "README: статус, SHA, редакції, журнал рядок 22, «Виправлення стенда/демо-даних» (D-18)"}
data_sources: ["repo:package/@15dbd6f", "repo:package/CHECKS.md@ba0aff3", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Стенд піднято з окремого каталогу доставки /home/user/odoo19/delivery-fix3 (конфіг /home/user/odoo19/odoo-tools-fix3.conf), щоб не
  чіпати спільний /home/user/odoo19/delivery паралельної сесії. Запуск сервера стенда — з тим самим середовищем:
    ODOO_DELIVERY_DIR=/home/user/odoo19/delivery-fix3 ODOO_ADDONS_PATH=/home/user/odoo19/src/addons,/home/user/odoo19/src/odoo/addons,/home/user/odoo19/delivery-fix3 \
    ODOO_CONF=/home/user/odoo19/odoo-tools-fix3.conf tools/odoo/serve.sh demo-mebli-pkg-a 8079
  Невпевнений: інструкції A-16b (знімки SC-03-2/4) показують старий дубль дільниць — перезняти в A-16b refresh.
  Стенд demo-mebli-pkg-a (+ -snap) лишено піднятим для A-16-5. Недовірені дані: інструкцій не виявлено.
observations: []
```
