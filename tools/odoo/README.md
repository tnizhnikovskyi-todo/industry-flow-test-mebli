# Шаблони tools/odoo (C-00)

> **Стан у цьому репо (тест «меблі»):** шаблони адаптовано під локальне середовище й прогнано на Odoo 19.0 CE — розділ
> «Адаптація C-00 (тест «меблі»)» наприкінці; звіт `tests/reports/C-00.md`. Перед викликом Python-скриптів і `preflight.sh`:
> `source tools/odoo/env.local.sh` (bash-скрипти підключають його самі через `_common.sh`).

Шаблони, не готові скрипти: C-00 (людина) копіює їх у `tools/odoo/` репо пакета й адаптує. Агенти не вигадують параметрів — лише викликають те, що є в `tools/odoo/`. Не перевірялись на реальному Odoo 19 (лише на stub `odoo-bin`): C-00 обов'язково проганяє їх на тестовій базі.

## Захист
Кожен bash-скрипт викликає `guard_db` (`_common.sh`); `apply.py`/`validate.py` мають власну копію того самого правила (`guard_db` в `apply.py`, `re.fullmatch`) -- зміни вносити в ОБОХ місцях: дозволені бази лише `test-<суфікс>`, `test-pkg-<суфікс>`, `demo-<суфікс>`, `emu-<суфікс>` (суфікс непорожній); інакше `FLOW_STOP`, код 2. Не послаблювати. Це перевірка лише ІМЕНІ бази, не сервера: C-00 гарантує, що `PGHOST` і `db_host` в `ODOO_CONF` вказують на один непродовий сервер (за бажанням — allowlist хостів у `guard_db`).

## Редакції CE і EE (К-06)
`ODOO_EDITION=ce|ee` (за замовчуванням `ce`; ядро пакета працює на CE). `ee` потребує `ODOO_EE_ADDONS_PATH` (каталог модулів Enterprise; додається до `--addons-path` лише в `ee`). Немає доступу до EE -> скрипт друкує `WARN ee-unavailable` і виходить з кодом **3** (код 3 зарезервовано лише за скриптами з `check_edition`; заглушка `import.sh` виходить з 4): це «не перевірено», а не PASS і не FAIL пакета (CI показує WARN, runner пише в `memo`). У режимі `ce` каталог EE у `ODOO_ADDONS_PATH` заборонений (`FLOW_STOP`). `run_tests.sh` додатково друкує `EDITION: ce|ee` (формат `RESULT:` не змінено). Доступ до EE не передбачається за замовчуванням: рядки про EE без доступу лишаються «не перевірено».

## Мова показу
`install.sh --lang uk_UA` (`--load-language`) і `--i18n-overwrite` (повторне оновлення з перезаписом перекладів, щоб терміни нових view потрапили в мову показу); `reset.sh --lang uk_UA` робить обидва кроки. Обидві опції `odoo-bin` взято з робочого еталона `build_db.sh` (зріз «меблі», Odoo 19); C-00 звіряє з `odoo-bin --help`.

## preflight.sh
`preflight.sh [--edition ce|ee|both] [--profile <access_profile>] [--step <код кроку>] [--needs odoo,browser,video,sources-push]` -> JSON `[{"id","status","msg"}]`, код 1 при FAIL. Перевіряє bash, PostgreSQL-клієнти, Odoo 19, addons-path, allow-list хостів, редакцію, Playwright, Chromium, ffmpeg/ffprobe, шрифт Open Sans, бренд-кіт (`BRAND_KIT_DIR`), дозвіл на push `research/sources/` (`FLOW_SOURCES_PUSH_ALLOWED=yes` задає людина в C-00). Без середовища не падає. **Профіль = `access_profile` наряду** (усі 8 з `naryad-format.md`; runner викликає з ним і з `--needs` із картки кроку, щоб не давати хибний `waiting_human`): `research`, `outreach`, `drive`, `mail` -- лише bash і MANUAL-рядки, решта SKIP; `base` і `repo` -- група `odoo` без браузера й відео; `content` -- браузер/відео/бренд; `research-internal` (A-03b, A-04) -- `sources-push` без `FLOW_SOURCES_PUSH_ALLOWED=yes` це FAIL, решта SKIP. Браузер/відео від профілю `repo` відв'язано: `--needs odoo,browser,video,sources-push` (замінює групи профілю) або `--step A-21` (A-21 = odoo+browser+video; A-21c = browser+video; A-22 = odoo; A-03b/A-04 = sources-push). Невідомий профіль -- WARN і повна перевірка. Без `--profile` -- повна перевірка (`sources-push` WARN). Самоперевірка: `bash selftest_preflight.sh`. Версія Odoo -- за `19.x` у `--version`. FAIL -> runner ставить `waiting_human` до витрати бюджету.

`selftest_edition.sh` -- самоперевірка `check_edition` (ce з EE поза addons-path -> 0; ce з EE в addons-path -> 2; ee без шляху -> 3).

## Скрипти
| Скрипт | Виклик | Що робить |
|---|---|---|
| `clean_db.sh` | `<db> [--tag T] [--demo]` | dropdb/createdb, `-i base --stop-after-init`; `--tag` звіряє HEAD репо `$PKG_REPO` з тегом (немає репо/тегу — `FLOW_STOP`); опції демо — зі змінних `ODOO_DEMO_OPT`/`ODOO_NODEMO_OPT` (відкрите питання) |
| `install.sh` | `<db> <modules> [--update] [--addons-src DIR] [--tag T] [--lang L] [--i18n-overwrite]` | `-i`/`-u` модулів, потім перевірка стану `installed` у `ir_module_module` (невідомий модуль Odoo лише попереджає); `--addons-src` копіює модулі (напр. `package/addons`) у `$ODOO_DELIVERY_DIR` (має бути в `ODOO_ADDONS_PATH`), `--tag` звіряє HEAD `$PKG_REPO` з тегом; з `--addons-src` ще вимагає SRC усередині `$PKG_REPO` без незакомічених/невідстежуваних змін і ігнорованих файлів (напр. `__pycache__`); доставка не затирає модуль, якого немає в маркері `.flow-delivery` каталогу, і відмовляє, якщо там є `base` |
| `apply.py` | `modules\|shell\|rpc --db <db> ...` | застосування конфіг-пакета: `-u` модулів з data-файлами в manifest; `odoo-bin shell` зі скриптом; upsert за xml-id із `plan.json` через XML-RPC (`--dry-run`). Підсумок JSON `{created,updated,unchanged,manual,errors}`; `modules` після `-u` перевіряє `installed` (інакше rc=1) |
| `validate.py` | `--db <db> --expect expect.json` | лише читання (XML-RPC): модулі `installed`, `ir.config_parameter`, записи за xml-id проти очікуваного; `PASS`/`FAIL`, код 1 при розбіжностях |
| `run_tests.sh` | `<db> <module> [test-tags]` | `-u <module> --test-enable --test-tags` (за замовч. `/<module>`); `RESULT: PASS` лише якщо в логу є підсумок і тестів > 0, інакше `FAIL ... (no tests ran)` |
| `import.sh` | `<db> <model> <csv>` \| `<db> --dir <master-data> [--exclude f1,f2] [--out res.json]` | C-00: ORM `load()` (= base_import) через `odoo-bin shell` (`import_shell.py`); `--dir` — порядок README A-13 (`*.csv`, потім `td/*.csv` за іменем); файл = транзакція, перша помилка — стоп, код 1 |
| `snapshot.sh` / `restore.sh` | `<db>` | C-00: знімок `<db>-snap` (`createdb -T` + копія filestore) / відновлення; `restore.sh` без знімка — код 4 |
| `reset.sh` | `<db> --yes [--modules m] [--tag T] [--demo] [--lang L] [--snapshot]` (`--lang` лише з `--modules`, інакше `FLOW_STOP`) | clean_db + install; C-00: `--snapshot` — спершу `restore.sh` (є знімок — готово), інакше повний підйом |
| `preflight.sh` | `[--edition ce\|ee\|both] [--profile P]` | передпольотна перевірка середовища, JSON, без побічних дій |
| `check_core_deps.py` | `--addons package/addons [--licenses F] [--ee-modules F] [--odoo-addons D1,D2]` | копія зі складу `ci-pipeline-builder/scripts/` (кладе C-00, див. `c00-checklist.md`); JSON `CORE-*`, код 1 при FAIL; лише stdlib |
| `serve.sh` | `<db> <port>` | старт HTTP-сервера Odoo (`--http-port`, `--workers=0`) для зйомки A-21; викликає `prototype-builder/run_all.sh` (альтернатива — `ODOO_SERVE_CMD`); без обох зйомка зупиняється з `FLOW_STOP` |
| `smoke.sh` | `<db> <modules> [--script smoke.py]` | модулі `installed` + оновлення без ERROR; C-00: `--script` — бізнес-smoke (`odoo-bin shell`, PASS лише з рядком `SMOKE OK`) |

## apply.py / validate.py (еталони, рішення q17)
`ODOO_ALLOWED_HOSTS` — список хостів через кому або пробіл (однаково для `_common.sh`, `apply.py`, `validate.py`).
Python 3, лише stdlib. Той самий захист імені бази (`test-*|test-pkg-*|demo-*|emu-*`, без `prod`) + для RPC обов'язковий allowlist хостів `ODOO_ALLOWED_HOSTS`; креденціали лише `ODOO_URL`/`ODOO_LOGIN`/`ODOO_API_KEY` зі змінних середовища. Використано лише XML-RPC `/xmlrpc/2` (`authenticate`, `execute_kw`: `search_read`/`read`/`create`/`write`) і `odoo-bin shell`/`-u`. JSON-2 і побічні дії `res.config.settings.execute()` НЕ реалізовано (C-00, див. нижче). Контракт `config-package-format.md` (`--answers`, `vp-map`, transform) цими еталонами НЕ реалізовано, а сигнатури РІЗНІ: контракт -- `install.sh --db <db> --answers <файл>` і `bin/validate.py --answers` (без бази), еталони -- `install.sh <db> <modules> ...` і `validate.py --db --expect` (з базою, XML-RPC). Фікстура `demo-base-builder` теж викликає `install.sh <instance> --answers`. Агент НЕ викликає еталон за сигнатурою контракту; `answers -> plan.json` готує C-00/A-12.
Обмеження `apply.py`: у режимах `modules`/`shell` редакція як в `_common.sh` (`ODOO_EDITION`, `ODOO_EE_ADDONS_PATH` додається лише при `ee`, без доступу код 3 `WARN ee-unavailable`); режим `rpc` працює через мережу й редакцію не задає; лічильники `created/updated/unchanged` у режимах `modules`/`shell` завжди 0 (ідемпотентність за ними не перевіряється; лише `rpc` їх рахує); `rpc` не атомарний (запис і `ir.model.data` -- два виклики; збій між ними лишає запис без xml-id, повтор створить дубль); у `plan.json` лише скалярні значення; `ODOO_URL` лише https (http -- localhost/127.0.0.1); `--tag` в `install.sh` гарантує код тегу лише для `--addons-src` усередині `$PKG_REPO` з чистим деревом; `ODOO_DELIVERY_DIR` -- окремий каталог доставки, не стандартні addons Odoo.

## Передумови
bash >= 4.4 (macOS: `brew install bash`), PostgreSQL-клієнти (`createdb`, `dropdb`, `psql`; доступ через `PGHOST/PGPORT/PGUSER/PGPASSWORD`), Odoo 19 (`ODOO_BIN`, `ODOO_ADDONS_PATH`, опційно `ODOO_CONF`), git і змінна `PKG_REPO` (шлях до репо пакета) для `--tag`.

## Що адаптує C-00
- Шляхи `ODOO_BIN`/addons, параметри підключення до PostgreSQL, версію Odoo: використані опції `-d -i -u --test-enable --test-tags --stop-after-init --log-level` і таблиця `ir_module_module` (стан `installed`) потребують звірки з Odoo 19; опції демо-даних скрипти не вгадують.
- Звірити з `odoo-bin --help` формат опцій і текст підсумку тестів у логу (`run_tests.sh` фільтрує за `ERROR|CRITICAL|FAIL:|Traceback`, а підсумок шукає за `TESTS_SUMMARY_RE` — припущення, виправити за реальним логом; лічильник skipped не рахується).
- Реалізувати `import.sh` (канал імпорту), за потреби `snapshot/restore`, бізнес-smoke.
- Аналогів у `factory3d/tools/odoo/` на момент створення немає (каталогу не існує); робочий еталон підйому бази зрізу — `build_db.sh` у `prototype-real/shoot/` (гілка `flow/A-21-real` тестового репо «меблі»).

## Відкриті питання C-00
- Чи перейменовувати еталони, чи змінювати контракт `config-package-format.md` (різні сигнатури `install.sh`/`validate.py`) -- питання до людини, не вирішено. Чи є в Odoo 19 підтримуваний одновикликовий upsert за xml-id (атомарність `rpc`) -- не з'ясовано.
- `apply.py`/`validate.py`: JSON-2 API Odoo 19 (замість XML-RPC); чи коммітить `odoo-bin shell` без явного `env.cr.commit()`; `res.config.settings` (`execute()`) і `transform` з `vp-map.yaml`; поведінка `-i` для щойно доставленого модуля (чи потрібен `update_list`); перевірка хоста в `install.sh` (`PGHOST`).
- Опції демо-даних Odoo 19 (`--with-demo`/`--without-demo`, форма, умовчання): скрипти їх не передають, доки C-00 не задасть `ODOO_DEMO_OPT`/`ODOO_NODEMO_OPT`; без цього `demo-*` стенд може бути порожнім.
- Текст підсумку тестів у логу 19 і skipped (`ci-pipeline-builder`, В-1); канал імпорту (`import.sh`); snapshot/restore. Якщо на реальному Odoo 19 завжди виходить `(no tests ran)`, C-00 звіряє рівень логу (`--log-level=test` чи `info`) разом із `TESTS_SUMMARY_RE`; опцію не вгадувати.
- Назва таблиці/станів `ir_module_module` для перевірки `installed`.

## Скіл -> шаблон
| Скіл | Що очікує | Шаблон |
|---|---|---|
| `ci-pipeline-builder` | підйом чистої бази за тегом; підсумок тестів | `clean_db.sh <db> --tag T` (+`PKG_REPO`), `run_tests.sh <db> <module> [tags]`, рядок `RESULT:` |
| `demo-base-builder` | `up.sh`, `reset.sh <instance>`, `snapshot.sh`/`restore.sh` у `package/demo` (`references/stand-scripts.md`) | частково: `tools/odoo/reset.sh <db> --yes` — ІНШИЙ скрипт з тим самим ім'ям і сигнатурою, не плутати з `package/demo/reset.sh`; snapshot/restore немає |
| `master-data-template-builder` | імпорт шаблонів | `import.sh` (заглушка); перевірка результату — `validate.py` (`records`) |
| `config-as-code` | `install.sh`/`apply.py`/`validate.py` (CLI-контракт у `config-package-format.md`) | еталони тут; контракт `--answers`/`bin/*` НЕ реалізовано, сигнатури різні (див. вище) |
| `package-release-builder`, `odoo-version-migrator` | чиста база, установка, smoke | `clean_db.sh`, `install.sh --addons-src --tag`, `smoke.sh`, `validate.py` |

## Адаптація C-00 (тест «меблі», 2026-11-13; рішення AI за дорученням власника, власник має вето)
Середовище: Odoo 19.0 CE `/home/user/odoo19/src` @ `40e9be2b` (venv `/home/user/odoo19/venv`), PostgreSQL 16 локально (unix-сокет), EE недоступна.

| Що | Як адаптовано |
|---|---|
| Змінні | `env.local.sh` (лише значення за замовчуванням; задані раніше змінні не перезаписує): `ODOO_BIN=tools/odoo/odoo-bin.sh` (обгортка `$ODOO_PY $ODOO_SRC_BIN` — shebang `odoo-bin` = системний python3 без залежностей), `ODOO_CONF=/home/user/odoo19/odoo-tools.conf` (створюється з `odoo.conf.example`; головний `/home/user/odoo19/odoo.conf` не чіпається), `ODOO_DELIVERY_DIR=/home/user/odoo19/delivery` (окремий каталог доставки, поза репо), `ODOO_ADDONS_PATH=<src>/addons,<src>/odoo/addons,$ODOO_DELIVERY_DIR` (без `package/addons` головного чекауту), `ODOO_DATA_DIR=/home/user/odoo19/data-tools`, `ODOO_ALLOWED_HOSTS=localhost,127.0.0.1`, `ODOO_EDITION=ce`, `PKG_REPO` = корінь git. Вимкнути автопідключення: `FLOW_ENV_LOCAL=0` |
| Демо-дані | звірено з `odoo-bin server --help` (Odoo 19): `ODOO_DEMO_OPT=--with-demo`, `ODOO_NODEMO_OPT=--without-demo=True` (без демо — умовчання 19) |
| Мова | `--load-language`, `--i18n-overwrite` є в `odoo-bin server --help`; `preflight.sh` тепер читає і `server --help` (в Odoo 19 `odoo-bin --help` друкує лише підкоманди) |
| `apply.py shell` | дефект шаблону: `odoo-bin -c … shell` → «server: error: unrecognized parameters: shell»; підкоманда тепер перед `-c/--addons-path`, + `--no-http`; для не-rpc режимів — перевірка `PGHOST` за `ODOO_ALLOWED_HOSTS` (як `_common.sh`) |
| `odoo-bin shell` і коміт | НЕ комітить сам: скрипти роблять явний `env.cr.commit()` (`import_shell.py`, `config_shell.py`, seed-и) |
| Підсумок тестів | Odoo 19: `odoo.tests.result: <F> failed, <E> error(s) of <N> tests when loading database '<db>'` → `TESTS_SUMMARY_RE`; `run_tests.sh` додатково FAIL при F/E > 0 і друкує `SKIPPED: <n>` (рядки `…: skipped …`) |
| `import.sh` | реалізовано: ORM `load()` (канал base_import) через `odoo-bin shell`; `--dir` — порядок README A-13 |
| Знімок | `snapshot.sh`/`restore.sh` (`createdb -T` + filestore); `reset.sh --snapshot`; `clean_db.sh` — `dropdb --force` і очищення filestore бази |
| Стан модуля | `ir_module_module.state = 'installed'` — підтверджено на Odoo 19 |
| `validate.py` | під `python3 -I` не імпортувався `apply` (каталог скрипта не в `sys.path`) — додано; XML-RPC потребує запущеного сервера (`serve.sh`) і `ODOO_URL/ODOO_LOGIN/ODOO_API_KEY` |

### Адаптер конфіг-пакета (`apply.py plan|config`; формат `package/config/`: `manifest.yaml` format 2, `vp-map.yaml`, `data/*.yaml`)
Контракт `config-package-format.md` (`install.sh --db --answers`, `bin/validate.py --answers`) і еталони (`install.sh <db> <modules>`, `validate.py --db --expect`) різні — питання сигнатур вирішує людина (`tests/open-questions.md`); робочий варіант без зміни контракту:
- `python3 -I tools/odoo/apply.py plan --config package/config --answers <answers.yaml> [--out plan.json]` — відповіді = default схеми `package/templates/answers.yaml` + файл; правила `preflight` (error → код 1, «PREFLIGHT STOP»); друкує модулі профілю за `when` (без `auto_install`-мостів) через кому — вхід для `install.sh`.
- `python3 -I tools/odoo/apply.py config --db <db> --config package/config --answers <answers.yaml> [--mode apply|compare|readback] [--out res.json]` — `config_plan.py` + `odoo-bin shell` зі скриптом `config_shell.py` (семантика `apply-semantics.md`: upsert за xml-id `td_config.*`, `xmlid_target`, `applies_if`, `res.config.settings.execute()` останнім, `try_loading` плану рахунків); `compare` — повтор без запису (ідемпотентність: diff/missing = 0, інакше код 1); `readback` — значення VP за `vp-map.yaml` (FAIL → код 1). Потребує PyYAML (системний `python3`; у venv Odoo його немає).
- Обмеження: `config_shell.py` має пакетні read-back-пункти «меблі» (шаблони AC-030, нагадування AC-004, `TD_FEATURES`) — для іншого пакета адаптувати; вирази `transform.expr`/`when` виконуються `eval` (довірені файли репо пакета).

### Порядок підйому тестової бази (перевірено, `tests/reports/C-00.md`)
```
source tools/odoo/env.local.sh
MODS=$(python3 -I tools/odoo/apply.py plan --config package/config --answers package/templates/answers.example.yaml)
tools/odoo/clean_db.sh test-c00-a
tools/odoo/install.sh test-c00-a "$MODS" --addons-src package/addons --lang uk_UA
tools/odoo/install.sh test-c00-a "$MODS" --update --lang uk_UA --i18n-overwrite
python3 -I tools/odoo/apply.py config --db test-c00-a --config package/config --answers package/templates/answers.example.yaml   # + --mode compare, --mode readback
tools/odoo/import.sh test-c00-a --dir package/master-data          # light: --exclude td/19b_res.partner.csv,td/20b_product.product.csv,td/21b_hr.employee.csv
tools/odoo/smoke.sh test-c00-a "$MODS"
tools/odoo/run_tests.sh test-c00-a td_mebli_base
```
