# Зауваження: flow-autocheck падає на службових ключах answers.yaml (A-09, 2026-11-13)

- Скіли: `flow-core:flow-autocheck` (scripts/autocheck.py, checks/A-09.yaml) ↔ `flow-package-build:questionnaire-builder` (references/answers-schema.md §2а).
- Що очікували: `answers-schema.md` §2а (нормативний) вимагає верхні ключі `edition` і `contract_mode` у схемі; `checks/A-09.yaml` має їх приймати (SKILL.md, перевірка `ED-edition`).
- Що вийшло: `parse_schema()` приймає лише ключі `VP-\d{2,3}` і кидає `ValueError: невідомий рядок схеми: edition:` — `vp-schema-keys` падає з трасою (весь прогін `--mode result` обривається, вердикту немає), `example-valid` → ERROR `schema-parse`. На копії схеми без службових ключів обидві перевірки — PASS. Перевірки `ED-edition` у checks/A-09.yaml немає (є лише в таблиці SKILL.md).
- Тип: (б) формат сусіднього скіла не збігається.
- Пропозиція: у `parse_schema()` пропускати/збирати `edition`, `contract_mode` (і не рахувати їх у `schema_keys`); додати `ED-edition` у checks/A-09.yaml; `--only` приймати кілька ID через кому (зараз — один).
- Дрібне: `answers-schema.md` §3 «example = усі не-deprecated VP, жодних зайвих ключів» — не сказано, чи йдуть туди `edition`/`contract_mode` (A-09 їх не вніс; default — у схемі).
- Дрібне: наряд A-08 (тест) мав `where: "a; b"` — `where_paths()` ділить лише за « + » і «, »; у наряді A-08-2 замінено на « + ».
