# Демо-стенд пакета «меблі» (A-15, спроба 2)

Скіл `flow-package-build:demo-base-builder` 0.3.1, режим «стенд пакета», старт 1. Скрипти — тонкі обгортки C-00 (`tools/odoo/`, README там).
Статус: стенд ce (модулі + конфіг A-12 + шаблони A-13) піднімається й скидається; **демо-шар `td_mebli_demo` падає — дефект D-01**
(`defects.md`, повернення в A-14). ee — не перевірено (EE недоступна).

## Адреса стенда
Локальний Odoo 19.0 CE середовища тесту, PostgreSQL 16 на `localhost`; база = `<instance>`, лише `demo-mebli-pkg-<суфікс>` (up.sh інше
ім'я відхиляє; `demo-mebli-full`, `demo-mebli-sample` стенд не чіпає). Веб-доступ: `tools/odoo/serve.sh <instance> <порт>` → `http://127.0.0.1:<порт>`.
Адреса хостингу для B-01 — відкрите питання Тімліду (В-4). Паролів тут немає.

## Ревізія package/ (commit SHA)
`SHA: 1925fb8afc25618d715ac1bfeefef64c8389d8dc` — ревізія `package/` (A-11-5), з якої зібрано стенд; гілка `flow/A-12-2-test` @ `b794c20`
(після неї змінено лише `tools/odoo/`, `tests/`, `flow/`). Мітка в `package/CHECKS.md` — `a5a10635…`; вердикт APPROVE (e887f26) охоплює
A-11-5 (№35–37), `git diff --stat 1925fb8..b794c20 -- package/` = лише `package/CHECKS.md`. Розбіжність мітки — `tests/open-questions.md`.

## Команда підйому з нуля
```
package/demo/up.sh <instance> ce                       # профіль package/demo/answers.yaml (A)
package/demo/up.sh <instance> ce --profile package/demo/profiles/answers.alt-<N>.yaml [--no-demo]
package/demo/up.sh <instance> ce --tag <тег пакета>    # A-18: спершу git checkout <тег> -- package/demo/
```
Кроки (кожен — виклик C-00, зупинка з кодом): preflight конфігу і модулі профілю (`apply.py plan`) → чиста база (`clean_db.sh`, 10) →
модулі `package/addons/` + «Модулі до установки» з `uk_UA` і перезаписом перекладів (`install.sh --addons-src`, 20) → конфіг A-12: прохід,
повтор (`--mode compare`, ідемпотентність), read-back (`apply.py config`, 30) → шаблони A-13, 28 кроків (`import.sh --dir`, 40) → демо-шар
`td_mebli_demo` + `data/seed_demo.py` + паролі ролей + бізнес-smoke `data/verify_demo.py` (`install.sh`, `apply.py shell`, `smoke.sh --script`, 50)
→ знімок (`snapshot.sh`, 60). `ee` без EE — 70. Без інтерактиву; лог — `package/demo/.logs/up-<instance>.log` (не в git).

## Команда скидання
`package/demo/reset.sh <instance> ce` — відновлює знімок `<instance>-snap` (`tools/odoo/restore.sh`: `createdb -T` + filestore, ~2 с;
ідемпотентно). Знімка немає — повний `up.sh <instance> ce [аргументи]` (fallback). Нічного скидання немає (рішення Тімліда).

## Редакції стенда
| редакція | SHA | статус | команда |
|---|---|---|---|
| ce | 1925fb8afc25618d715ac1bfeefef64c8389d8dc | піднято без демо-шару (модулі, конфіг, шаблони A-13); демо-шар — D-01 | `up.sh <i> ce` |
| ee | 1925fb8afc25618d715ac1bfeefef64c8389d8dc | не перевірено (EE недоступна; `up.sh <i> ee` → код 70) | `up.sh <i> ee --profile package/demo/profiles/answers.alt-4.yaml` |
Мости `td_mebli_*` EE (shopfloor, quality, fsm, planning, helpdesk, sign) — лише на ee; на ce `uninstalled`. Ядро `td_*` — без EE-залежностей.

## Режим використання стенда
Відкрите питання: режим обирає Тімлід (окремі інстанси чи один стенд із журналом бронювання). Скрипти параметризовані `<instance>`, тож
підтримують обидва: окремий інстанс на споживача (A-16, кожне демо B-01, D-03, тест A-18). Тест оновлення A-18 — база піднімається
скриптами `package/demo/` з попереднього тегу: `git checkout <тег> -- package/demo/` → `up.sh <instance> ce --tag <тег>`; скрипти не
посилаються на файли поза `package/` і `tools/odoo/`.

## Демо-ролі й логіни
Ролі й групи — `plan.md` §2 (логіни `<роль>@demo-fabryka.example`: salon, salon2, salon3, tech, chief, store, fin, owner, measure, fitter,
fitter2, tablet). Паролі — змінна `DEMO_USERS_PASSWORD` під час `up.sh` (сховище секретів — рішення Тімліда, В-4); без неї діють паролі
модуля `td_mebli_demo`. Ролі створює демо-шар — до виправлення D-01 на стенді є лише `admin`.

## Склад демо-даних
- Шаблони A-13 `package/master-data/` (28 файлів, 97 рядків, xml-id `td_md.*`) — усі «Демо-…», без контактів.
- Демо-шар — модуль `td_mebli_demo` (каталог, робочі центри, склад, партії листів, обрізки) + `seed_showcase` (документи й історія:
  на налаштованій базі 124 замовлення, 110 MO, 49 закупівель, 123 задачі монтажу, 2209 партій — діагностичний прогін без коміту, D-01).
  Seed детермінований (`random.Random(2026)`, `Random(7)` у модулі); дати — від дня підйому (`now()`), фіксованої дати відліку немає.
- Синтетичні контакти: розділу в `package/DATA_POLICY.md` немає — телефони `+380 00 000 00 NN` (вигаданий діапазон), e-mail у зарезервованому
  домені `.example` (`demo-fabryka.example`, `mail.example`, `client-demo.example`); ЄДРПОУ/IBAN не вносяться. Люди й клієнти в
  `td_mebli_demo` мають вигадані ПІБ, а не назви ролей — відхилення від `demo-data-rules.md`, питання Тімліду (`tests/open-questions.md`).
- `package/demo/data/` — лише скрипти (seed, паролі, smoke); синтетики в CSV тут немає (не дублюємо модуль).

## Файл answers.yaml і профілі
| профіль | VP, що змінені (від `answers.yaml`) | сценарії | результат установки |
|---|---|---|---|
| `answers.yaml` (A, ce) | — (= `answers.example.yaml` + `edition: ce`, `contract_mode: unset`) | UC-01…UC-08 | модулі 43 (137 installed) OK; конфіг 8/4/14, повтор unchanged 26, read-back 23/23 PASS; A-13 28/28 (97 рядків); демо-шар — **FAIL D-01** (код 50); з `--no-demo` — OK, smoke OK, знімок OK |
| `alt-1` (light, ce) | VP-01 light, VP-04 false, VP-05 false, VP-08 true, VP-09 distributor, VP-10 1, VP-11 1, VP-13 1, VP-17 flexible, VP-18 false, contract_mode sale | UC-01, UC-02 (порізка в дистриб'ютора) | модулі 42 (136, без `td_mebli_bas`) OK; конфіг 8/13/1 (skipped 7 за PF-03…PF-08), повтор unchanged 22, read-back 23/23 PASS; A-13 25/25 (91 рядок, без td/19b–21b); демо-шар не ставиться; smoke OK |
| `alt-2` (B, ce) | VP-01 B, VP-02 + ai_mapping, VP-03 multi_install_fop, VP-06 block, VP-07 7, VP-10 30, VP-11 50, VP-12 1000, VP-13 60, VP-14 time, VP-15 stage, VP-16 false, VP-17 strict, contract_mode contract | UC-05, UC-08 (ФОП-бригади) | модулі 44 (138, `td_mebli_multico` installed) OK; конфіг 8/15/4, повтор unchanged 27, read-back 23/23 PASS; A-13 28/28; `--no-demo`; smoke OK |
| `alt-3` (B, ce) | VP-01 B, VP-02 [configurator, kiosk, quality], VP-03 multi, VP-07 1, VP-12 100 | UC-03 | модулі 43 (137, `td_mebli_multico` uninstalled) OK; конфіг 8/7/12, повтор unchanged 27, read-back 23/23 PASS; A-13 28/28; `--no-demo`; smoke OK |
| `alt-4` (C = B + ee) | VP-01 B, edition ee | мости EE | не перевірено: `up.sh … ee` → код 70 (WARN ee-unavailable), до установки |

Покриття значень (кожне допустиме значення enum/bool/multi схеми A-09 — хоча б в одному файлі; int — у межах min/max схеми):
| VP-xx | значення | де покрито | профіль встановлено |
|---|---|---|---|
| VP-01 | light / A / B | alt-1 / answers / alt-2, alt-3 | так / так / так |
| VP-02 | configurator, offcut, cutting_batch, kiosk, quality, label_scan, change_sign, nbu, analog, shop_board / ai_mapping | answers, alt-2 / alt-2 | так (застосовується лише при B) |
| VP-03 | single / multi / multi_install_fop | answers / alt-3 / alt-2 | так / так / так |
| VP-04 | true / false | answers / alt-1 | так / так |
| VP-05 | true / false | answers / alt-1 | так / так |
| VP-06 | warn / block | answers / alt-2 | так / так |
| VP-07 | 1 / 2 / 7 (int 1–7) | alt-3 / answers / alt-2 | так |
| VP-08 | false / true | answers / alt-1 | так / так |
| VP-09 | both / distributor | answers / alt-1 | так / так |
| VP-10 | 1 / 5 / 30 (int 1–30) | alt-1 / answers / alt-2 | так |
| VP-11 | 1 / 5 / 50 (int 1–50) | alt-1 / answers / alt-2 | так |
| VP-12 | 100 / 300 / 1000 (int 100–1000) | alt-3 / answers / alt-2 | так |
| VP-13 | 1 / 14 / 60 (int 1–60) | alt-1 / answers / alt-2 | так |
| VP-14 | equal / time | answers / alt-2 | так / так |
| VP-15 | final / stage | answers / alt-2 | так / так |
| VP-16 | true / false | answers / alt-2 | так / так |
| VP-17 | flexible / warning / strict | alt-1 / answers / alt-2 | так / так / так |
| VP-18 | true / false | answers / alt-1 | так / так |
| edition | ce / ee | answers, alt-1…3 / alt-4 | так / ні — EE недоступна (не перевірено) |
| contract_mode | unset / sale / contract | answers, alt-3 / alt-1 / alt-2 | так / так / так |
Профілі alt-2, alt-3 піднято з `--no-demo` (перевірка установки й конфігу); alt-1 (light) демо-шар не має (залежність `td_mebli_bas`).

## Журнал установки
Дата 2026-11-13, Odoo 19.0 CE @ `40e9be2b`, PostgreSQL 16 (локально), `package/` @ `1925fb8`, гілка @ `b794c20`; конфіг формат 2 (`apply.py config`).
| крок | що встановлено | команда | результат (код) | тривалість |
|---|---|---|---|---|
| 1 | A: модулі + конфіг + A-13 + демо-шар | `up.sh demo-mebli-pkg-a ce` | FAIL на «демо-документи (seed)» (50) — D-01; кроки 0–4 і установка `td_mebli_demo` — OK | 213 с |
| 2 | A без демо-шару | `up.sh demo-mebli-pkg-a ce --no-demo` | OK (0): 43 модулі (137 installed, `web_enterprise` немає), VP за `answers.yaml` — read-back 23/23, A-13 28/28, smoke, знімок | 283 с |
| 3 | скидання | змінено `td_md.product_category_raw.name` → `reset.sh demo-mebli-pkg-a ce` | OK (0): зі знімка, назва повернулась «Сировина» | 2 с |
| 4 | alt-1 light | `up.sh demo-mebli-pkg-a-p1 ce --profile …alt-1.yaml` | OK (0), демо-шар пропущено (light) | 274 с |
| 5 | alt-2 B | `up.sh demo-mebli-pkg-a-p2 ce --profile …alt-2.yaml --no-demo` | OK (0) | 279 с |
| 6 | alt-3 B multi | `up.sh demo-mebli-pkg-a-p3 ce --profile …alt-3.yaml --no-demo` | OK (0) | 280 с |
| 7 | alt-4 ee | `up.sh demo-mebli-pkg-a-p4 ee --profile …alt-4.yaml` | 70 — EE недоступна, «не перевірено» | 0 с |
Діагностика D-01 (scratch, без коміту): `seed_showcase` без перейменування податків проходить (124 SO, 110 MO, 49 PO, 123 задачі, 2209 партій).
Бази `demo-mebli-pkg-*` після кроку видалено (стенд — код у git; підйом — команда вище).

## Виправлення стенда/демо-даних
Немає (старт 1; повернень з A-16 не було).
