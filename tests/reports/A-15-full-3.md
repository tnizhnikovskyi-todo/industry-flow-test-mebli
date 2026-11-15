# Звіт кроку A-15 (демо-стенд, повний перепідйом, контур коду 3) — тестовий режим

Наряд: `tests/naryad/A-15-full-3.yaml`. Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета», повний перепідйом після A-14-7. Гілка `flow/A-15-full-3-test` від `flow/A-14-7-test` @ `dd1c949`.

```yaml
run: {step: A-15, scope: package/mebli, attempt: full-3, started: 2026-11-15T23:27:00Z, finished: 2026-11-15T23:50:00Z}
result: done
partial: true
pr: "PR не створено (наказ сесії); гілка flow/A-15-full-3-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 50000, tokens_out: 6000, agent_hours: 0.4}   # оцінка
cost_estimated: true
sha_stand: dd1c9490f637c8c33fdbf983d22ab749d2763af9
checks:
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався; бази лише demo-mebli-pkg-a(-snap); demo-mebli-full / -sample не чіпались"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND dd1c949 — нащадок SHA CHECKS.md 1778db7 (A-14-7, APPROVE (CE); EE не перевірено); diff package/ = лише CHECKS.md"}
  - {id: up-from-scratch, status: PASS, msg: "окремий каталог доставки /home/user/odoo19/delivery-fix4 (конфіг odoo-tools-fix4.conf); DEMO_REPORT_URL=http://127.0.0.1:8079 up.sh demo-mebli-pkg-a ce → 0, 731 с, без ручних кроків"}
  - {id: modules-installed, status: PASS, msg: "47 модулів профілю + td_mebli_demo, 142 installed; td_home_menu 1.0.1, td_knowledge 1.1.2, td_mebli_dashboard 1.1.3, td_mebli_measure 1.1.4, td_mebli_notify 1.1.4"}
  - {id: config-answers, status: PASS, msg: "apply, повтор, read-back до й після демо-шару — OK"}
  - {id: smoke, status: PASS, msg: "SO 124, MO 110, PO 49, задачі 123, партії 2213, td_md xmlid 80, ролі з групами, tech technologist true, 4 дільниці"}
  - {id: icons-home, status: PASS, msg: "web_icon кореневих меню td_*: td_knowledge / td_mebli_dashboard / td_mebli_measure,static/description/icon.png; головний екран під salon, admin, owner, measure на 1440×900 і 390×844 — навбар лише systray, підписи в один рядок (розривів посеред слова 0), горизонтальної прокрутки немає, помилок сторінки 0"}
  - {id: reset, status: PASS, msg: "змінено partner_salon → reset.sh → назва й 124 SO повернулись, 1 с"}
  - {id: profiles-coverage, status: SKIP, msg: "alt-1…5 не перепіднімались: профілі й конфіг не змінено; регрес A/light/B — C-03 A-14-7 (0 failed)"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна)"}
  - {id: readme-sections, status: PASS, msg: "README: статус, SHA, редакції, журнал рядки 23–24, «Виправлення стенда/демо-даних»"}
data_sources: ["repo:package/@dd1c949", "repo:package/CHECKS.md@1778db7", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Сервер стенда — з тим самим середовищем:
    ODOO_DELIVERY_DIR=/home/user/odoo19/delivery-fix4 ODOO_ADDONS_PATH=/home/user/odoo19/src/addons,/home/user/odoo19/src/odoo/addons,/home/user/odoo19/delivery-fix4 \
    ODOO_CONF=/home/user/odoo19/odoo-tools-fix4.conf tools/odoo/serve.sh demo-mebli-pkg-a 8079
  Знімки головного екрана ПІСЛЯ (не в git): /home/user/industry-flow-test-mebli/docs/industries/mebli/home-menu-review/after-{salon,admin,owner,measure}-{1440x900,390x844}.png.
  Невпевнений: на 1440 підписи «Обслуговування», «Виставлення рахунків» — з «…» (колонка ≈ 118 px; рішення власника — ellipsis + title); на 390 — «Обслуговування» повністю.
  AI-30 уточнено (AI-DECISIONS). Стенд лишено для A-16-6. Недовірені дані: інструкцій не виявлено.
observations: []
```
