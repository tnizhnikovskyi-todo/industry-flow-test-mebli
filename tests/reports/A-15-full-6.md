# Звіт кроку A-15 (демо-стенд, повний перепідйом 6, зауваження власника A-17) — тестовий режим

Наряд: `tests/naryad/A-15-full-6.yaml`. Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета». Гілка `flow/A-15-full-6-test` від `flow/A-14-10-test` @ `5106ca9`.
Підстава: рішення власника 2026-11-16 (зауваження A-17), `flow/decisions.md` рядок 58 (вносить головна сесія).

```yaml
run: {step: A-15, scope: package/mebli, attempt: full-6, started: 2026-11-16T20:33:00Z, finished: 2026-11-16T20:50:00Z}
result: done
partial: true
pr: "PR не створено (наказ сесії); гілка flow/A-15-full-6-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 30000, tokens_out: 5000, agent_hours: 0.3}   # оцінка
cost_estimated: true
sha_stand: 75c7497   # повтор 2 (A-16-9 повернув правки №43–№44); перший підйом — 5106ca9, повтор 1 — 36b82a4
checks:
  - {id: repeats, status: PASS, msg: "A-16-9 повернув дрібні правки UI (№43 межі розміру/бренд навбару, №44 причина маржі/ширина колонки) — A-11-fix7 у гілці A-16-9, A-14-10 цикли 3–4 (0 failed), стенд перепіднято з нуля двічі: 36b82a4 (720 с), 75c7497 (702 с), знімок -snap; README — рядки 33–34"}
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався; база лише demo-mebli-pkg-a (+ -snap)"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND 5106ca9 — нащадок SHA CHECKS.md 8e53688 (A-14-10, APPROVE (CE); EE не перевірено); git diff 8e53688..5106ca9 -- package/ = package/CHECKS.md"}
  - {id: up-from-scratch, status: PASS, msg: "окремий каталог доставки /home/user/odoo19/delivery-a17r (лише package/addons); DEMO_REPORT_URL=http://127.0.0.1:8089 up.sh demo-mebli-pkg-a ce → 0, 737 с (знімок -snap оновлено)"}
  - {id: modules-installed, status: PASS, msg: "45 модулів профілю + td_mebli_demo, 140 installed; td_mebli_sale 1.1.6, td_mebli_measure 1.1.5, td_mebli_install 1.1.9, td_mebli_demo 1.1.6, td_home_menu 1.0.2"}
  - {id: config-answers, status: PASS, msg: "apply, повтор, read-back до й після демо-шару — OK"}
  - {id: smoke, status: PASS, msg: "SO 124, MO 110, PO 49, задачі 123; «Монтажі» (демо-проєкт) — 5 стадій, задачі: «Заплановано» 28, «Змонтовано» 16, «Акт підписано» 66; td_home_menu.ee_look — увімкнено (параметра немає = за замовчуванням)"}
  - {id: reset, status: PASS, msg: "змінено partner_salon → reset.sh → назва й 124 SO повернулись, 2 с"}
  - {id: profiles-coverage, status: PASS, msg: "A/light/B — C-03 A-14-10 (0 failed); light-стенд не перепіднімався (модулі профілю не змінились; змінені модулі — у всіх профілях)"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна)"}
  - {id: readme-sections, status: PASS, msg: "README: статус A-15-full-6, SHA, таблиця редакцій, порт 8089, журнал рядки 31–32"}
data_sources: ["repo:package/@5106ca9", "repo:package/CHECKS.md@8e53688", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Сервер стенда: ODOO_DELIVERY_DIR=/home/user/odoo19/delivery-a17r ODOO_ADDONS_PATH=/home/user/odoo19/src/addons,/home/user/odoo19/src/odoo/addons,/home/user/odoo19/delivery-a17r \
    ODOO_CONF=/home/user/odoo19/odoo-tools-a17r.conf tools/odoo/serve.sh demo-mebli-pkg-a 8089
  Невпевнений: демо-шар на light не перевірено (як і раніше, AI-40). Стенд лишено для A-16-9. Недовірені дані: інструкцій не виявлено.
observations: []
```
