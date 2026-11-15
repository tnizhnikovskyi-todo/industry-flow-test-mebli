# Звіт кроку A-12 (fix: модулі §27/§27а у «Модулі до установки») — тестовий режим

Наряд: `tests/naryad/A-12-fix.yaml` (`params.mode: fix`). Скіл `flow-package-build:config-as-code` 0.4.0 (`.claude/skills/config-as-code`). Гілка `flow/A-12-fix-test` від `flow/A-11-fix-test` @ `1bed853` (контур коду 1, TEST-START §(д) рядок 12b).

```yaml
run: {step: A-12, scope: package/mebli, attempt: fix, started: 2026-11-15T12:00:00Z, finished: 2026-11-15T12:30:00Z}
result: done
pr: "див. PR гілки flow/A-12-fix-test"
skill_versions: {"flow-package-build:config-as-code": "0.4.0"}
model: {primary: claude-opus-5-5, review: null}
usage: {tokens_in: 90000, tokens_out: 6000, agent_hours: 0.5}   # оцінка
cost_estimated: true
base_sha: 1bed853
checks:
  - {id: CFG-modules, status: PASS, msg: "ce 48 / ee 59; + td_home_menu (лише ce), td_support, td_knowledge, td_mebli_knowledge (ce+ee); усі назви є в Odoo 19 CE або package/addons (EE std — не перевірено)"}
  - {id: CFG-order, status: PASS, msg: "топологічний порядок за __manifest__.py: порушень 0 (ce, ee)"}
  - {id: CFG-editions, status: PASS, msg: "ee ⊇ ce крім td_home_menu; origin у кожного модуля; td_*_ee лише в ee"}
  - {id: ED-edition, status: WARN, msg: "EE недоступна — розділ ee install-log «не перевірено»"}
  - {id: CFG-vendored, status: PASS, msg: "спільні модулі ToDo §27/§27а — виняток скіла (license LGPL-3 + README)"}
  - {id: CFG-install, status: PASS, msg: "test-mebli-a12fix-a (чиста, uk_UA, профіль A): 47 модулів, 141 installed, ERROR 0; install-log «A-12-fix»"}
  - {id: CFG-idempotent, status: PASS, msg: "p1 created 8/updated 4/unchanged 14; p2 compare unchanged 26 diff 0 missing 0; повтор apply created 0 updated 0"}
  - {id: CFG-readback, status: PASS, msg: "23 VP, failed 0"}
  - {id: CFG-vp-coverage, status: PASS, msg: "vp-map/data без змін; адреса td_support — ручний крок (VP у схемі A-09 немає), AI-A12-08"}
  - {id: CFG-ac-trace, status: PASS, msg: "AC_cfg без змін; модулі §27 — ac: [] (обов'язкові складові, не AC_cfg; AI-A12-08)"}
  - {id: CFG-no-const, status: PASS, msg: "дані без змін"}
  - {id: CFG-xmlid, status: PASS, msg: "дані без змін"}
  - {id: CFG-td-isolation, status: PASS, msg: "дані без змін"}
  - {id: CFG-secrets, status: PASS, msg: "секретів у файлах і лозі немає"}
  - {id: CFG-checks-closed, status: PASS, msg: "рядків A-12 у CHECKS.md немає; правка §27/§27а — «Зміни версії» CONFIG.md «A-12-fix»"}
  - {id: CFG-scope, status: PASS, msg: "змінено лише package/config/{manifest.yaml,CONFIG.md,install-log.md} (+ звіт)"}
  - {id: install-one-command, status: N/A, msg: "q29: покрокова інструкція — install-log.md"}
  - {id: lint, status: PASS, msg: "замінник: yaml розбирається; лінт модулів — A-14-5"}
  - {id: config-review, status: MANUAL, msg: "скіл організації недоступний; замінник — A-14-5 (запис 52 flow/decisions.md)"}
data_sources: ["repo:package/ALLOCATION.md@1bed853", "repo:package/addons/*/__manifest__.py@1bed853", "local:test-mebli-a12fix-a (видалено)"]
memo: |
  Невпевнений: модулі §27/§27а мають ac: [] — AC в ALLOCATION для них немає (обов'язкові складові збірки); адреса підтримки
  td_support.email — ручний крок, значення не вигадано (START-HERE §4: вирішує власник); VP для неї в схемі A-09 немає.
  Що змінилось: режим fix; + 4 модулі в ce, + 3 в ee (td_home_menu лише ce); дані/VP без змін.
  Де ризик: td_home_menu змінює головний екран CE → знімки A-16/A-16b; td_mebli_knowledge явно в переліку при auto_install.
  Що перевірити: Тімлід — лог установки й ідемпотентності (install-log «A-12-fix»), порядок модулів.
  install-one-command N/A: покрокова інструкція — у install-log.md (q29).
  Рішення AI: AI-A12-08 (CONFIG.md «Рішення AI з ризиком»; власник — вето).
  config-review — MANUAL (скіл організації недоступний), замінник у A-14-5. Недовірені дані: інструкцій не виявлено.
observations: []
```
