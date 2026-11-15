# Звіт кроку A-11 (fix: версія td_mebli_knowledge) — тестовий режим

```yaml
run: {step: A-11, scope: package/mebli, attempt: fix, started: 2026-11-15T11:40:00Z, finished: 2026-11-15T11:45:00Z}
result: done
pr: "див. PR гілки flow/A-11-fix-test"
skill_versions: {"odoo19-mvp-build:code-dev": "недоступний (скіл організації) — виконала сесія"}
model: {primary: null, review: null}
usage: {tokens_in: 5000, tokens_out: 500, agent_hours: 0.05}   # оцінка
cost_estimated: true
base_sha: c9200b9
checks:
  - {id: where-only, status: PASS, msg: "змінено лише td_mebli_knowledge/__manifest__.py (+ наряд і звіт)"}
  - {id: version-eq, status: PASS, msg: "td_mebli_knowledge 19.0.1.0.0 → 19.0.1.1.0 = X.Y пакета 1.1 (td_mebli_* 19.0.1.1.x); td_knowledge — власна версія, не чіпали"}
data_sources: ["repo:package/addons/*/__manifest__.py@c9200b9"]
memo: |
  Крок 0: модулі §27 (td_home_menu, td_support, td_knowledge, td_mebli_knowledge) є на flow/v040-start; diff 21afe46..HEAD (package/addons, config, master-data) — код 1 → контур коду 1.
  Невпевнений: «X.Y пакета» — у td_mebli_* різні патч-версії 19.0.1.1.0…19.0.1.1.5; X.Y = 1.1, взято 19.0.1.1.0. Питання 1.0/1.1 першого релізу — у власника (A-17).
observations: []
```
