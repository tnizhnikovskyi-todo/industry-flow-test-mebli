# Зауваження: шаблони tools/odoo (flow-core/references/templates/tools-odoo/) на реальному Odoo 19.0 CE (C-00, 2026-11-13)

- Плагін: flow-core (шаблони `references/templates/tools-odoo/`), споживачі — demo-base-builder (A-15), ci-pipeline-builder, master-data-template-builder, config-as-code.
- Що очікували: шаблони запускаються після підстановки змінних середовища.
- Що вийшло (виправлено в `tools/odoo/` цього репо, джерело правди — плагін, не правилось):
  1. `apply.py shell`: `odoo-bin -c <conf> --addons-path=… shell -d …` → Odoo 19: «server: error: unrecognized parameters: shell» — підкоманда має йти перед `-c` (з `ODOO_CONF` режим shell не працює взагалі; `build_db.sh` A-21 теж кличе `apply.py shell`). (а)
  2. `validate.py` під `python3 -I` не імпортує `apply` (каталог скрипта не в `sys.path`), а скіли кличуть Python-скрипти з `-I`.
  3. `preflight.sh` (`odoo-lang-opts`): в Odoo 19 `odoo-bin --help` друкує лише підкоманди; `--load-language`/`--i18n-overwrite` є в `odoo-bin server --help` — хибний WARN.
  4. `run_tests.sh`: `TESTS_SUMMARY_RE` за замовчуванням ловить і рядок Odoo 19 `odoo.tests.result: 0 failed, 0 error(s) of N tests …`, але «N failed» > 0 при коді 0 не перевіряється — додано.
  5. `selftest_preflight.sh` очікує `core-deps-script=WARN`, хоча C-00 за чек-листом кладе `check_core_deps.py` поруч — після C-00 самоперевірка падає.
  6. `odoo-bin` має shebang системного `python3`; у venv-установці `ODOO_BIN` має бути обгорткою — у README шаблонів не згадано.
- Пропозиція: внести 1–6 у шаблони плагіна; задокументувати Odoo 19: `--with-demo` / `--without-demo=BOOL` (умовчання — без демо), `odoo-bin shell` не комітить без `env.cr.commit()`, XML-RPC позначено застарілим (ERROR-рядки в лозі сервера). (г)
