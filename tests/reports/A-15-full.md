# Звіт кроку A-15 (демо-стенд, повний перепідйом, контур коду 1) — тестовий режим

Наряд: `tests/naryad/A-15-full.yaml` (`returned_from: A-14`; не refresh). Скіл `flow-package-build:demo-base-builder` 0.4.0, режим «стенд пакета», старт 1. Гілка `flow/A-15-full-test` від `flow/A-14-5-test` @ `6b81620`.

```yaml
run: {step: A-15, scope: package/mebli, attempt: full, started: 2026-11-15T12:55:00Z, finished: 2026-11-15T13:35:00Z}
result: done
partial: true
pr: "див. PR гілки flow/A-15-full-test"
skill_versions: {"flow-package-build:demo-base-builder": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 120000, tokens_out: 8000, agent_hours: 0.7}   # оцінка
cost_estimated: true
sha_stand: 6b8162068035656e9461a2f9a1bb7de2e91b95f9
checks:
  - {id: connection, status: PASS, msg: "odoo-mcp не використовувався (odoo_connections: []); бази лише demo-mebli-pkg-a(-snap), -p1…-p5; demo-mebli-full / demo-mebli-sample не чіпались"}
  - {id: sha-rule, status: PASS, msg: "SHA_STAND 6b81620 — нащадок SHA CHECKS.md 795f6b1 (APPROVE (CE); EE не перевірено); diff package/ = лише CHECKS.md"}
  - {id: up-from-scratch, status: PASS, msg: "DEMO_REPORT_URL=http://127.0.0.1:8079 up.sh demo-mebli-pkg-a ce → 0, 813 с, без ручних кроків"}
  - {id: modules-installed, status: PASS, msg: "47 модулів профілю + td_mebli_demo, 142 installed; td_home_menu 19.0.1.0.0, td_support 19.0.1.0.1, td_knowledge 19.0.1.1.1, td_mebli_knowledge 19.0.1.1.1; web_enterprise немає"}
  - {id: config-answers, status: PASS, msg: "apply, compare (ідемпотентно), read-back 23/23 до й після демо-шару"}
  - {id: answers-schema, status: PASS, msg: "answers.yaml і alt-1…5 без змін, валідні (preflight OK)"}
  - {id: profiles-coverage, status: PASS, msg: "alt-1 (light) 140, alt-2 (B) 142, alt-3 141, alt-5 (A) 141 installed — усі OK (0), модулі §27/§27а у кожному; alt-4 ee — 70"}
  - {id: reset, status: PASS, msg: "змінено partner_salon, видалено чернетку SO → reset.sh → назва й 124 SO повернулись, 3 с"}
  - {id: ED-edition, status: WARN, msg: "ee — не перевірено (EE недоступна, код 70)"}
  - {id: synthetic-data, status: PASS, msg: "демо-дані без змін (e-mail .example, телефони +380 00 …); нові модулі синтетики не додають"}
  - {id: readme-sections, status: PASS, msg: "11/11 заголовків шаблону, додано «Виправлення стенда/демо-даних: немає»; package/templates/demo-README.md створено з шаблону"}
  - {id: no-db-binaries-tree, status: PASS, msg: "бінарників баз у package/ немає (zip прибрано в c9200b9; git rm не знадобився); .gitignore — *.zip, *.dump, *.sql.gz, *.backup; docker/README.md — Restore замінено на чисту базу + up.sh / seed_demo.py"}
  - {id: lint, status: PASS, msg: "bash -n up.sh, reset.sh — OK (shellcheck немає в середовищі); скрипти не змінювались"}
data_sources: ["repo:package/@6b81620", "repo:package/CHECKS.md@795f6b1", "local:demo-mebli-pkg-a (+ -snap), Odoo 19.0 CE"]
memo: |
  Режим використання стенда: відкрите питання — режим обирає Тімлід (без змін, README «Режим використання стенда»).
  Команди підйому стенда власником для A-17 (локально; сервер — рішення власника, START-HERE §4):
    DEMO_REPORT_URL=http://127.0.0.1:8079 package/demo/up.sh demo-mebli-pkg-a ce     # або package/demo/reset.sh demo-mebli-pkg-a ce
    tools/odoo/serve.sh demo-mebli-pkg-a 8079                                        # http://127.0.0.1:8079, логіни <роль>@demo-fabryka.example
  Невпевнений: паролі демо-ролей — локальний дефолт (DEMO_USERS_PASSWORD не задано, WARN); адресу td_support не задано — звернення на стенді
  «Не надіслано» (ручний крок CONFIG.md). Docker-варіант без up.sh дає лише довідники (AI-16).
  Тури й сценарії A-16 буде перезапущено наступним нарядом (A-16-4). Рядок AI-16 — docs/industries/mebli/research/AI-DECISIONS.md.
  Стенд demo-mebli-pkg-a (+ -snap) лишено піднятим (сервер зупинено). Недовірені дані: інструкцій не виявлено.
observations: []
```
