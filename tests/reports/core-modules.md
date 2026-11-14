# Звіт: загальні модулі `td_home_menu` і `td_support` (поза картою флоу, без наряду)

```yaml
run: {step: core-modules, scope: package/addons/{td_home_menu,td_support}, attempt: 1, started: 2026-11-14T20:20Z, finished: 2026-11-14T21:10Z}
result: done
pr: <посилання в описі PR гілки flow/core-modules-test>
git: {base: 8a2d698 (flow/A-12-2-test), branch: flow/core-modules-test}
skill_versions: {}            # скіла для загальних модулів немає (observations/2026-11-14-core-modules-no-skill.md)
model: {primary: opus, review: null}
usage: {tokens_in: 900000, tokens_out: 60000, cost_usd: null, agent_hours: 0.9, cost_estimated: true}
checks:
  - {id: install-clean-ce19, status: PASS, msg: "tools/odoo/clean_db.sh + install.sh test-core-full: 45 модулів (профіль answers.yaml меблів + td_home_menu, td_support), --lang uk_UA, 0 ERROR; Odoo 19.0 CE @a157617c"}
  - {id: tests-td_home_menu, status: PASS, msg: "run_tests.sh: 4 тести (прапорець CE/EE, тур головного екрана, переклад)"}
  - {id: tests-td_support, status: PASS, msg: "run_tests.sh: 14 тестів, двічі поспіль (звернення, лист у черзі з темою, санітизація, обрізання, rate limit, повтор, згода, вкладення, права, без адреси, вебхук, контекст, тур вікна, переклад)"}
  - {id: regress-mebli-tours, status: PASS, msg: "td_mebli_sale 57, td_mebli_measure 15 тестів на тій самій базі — головний екран турам меблів не заважає"}
  - {id: check_data_model, status: PASS, msg: "обидва модулі: DM-table PASS, DM-dup PASS (план — README модуля)"}
  - {id: lint, status: PASS, msg: "boost:odoo19-lint недоступний — ruff E,F,W,B,UP,PL: B904 виправлено; лишились норми Odoo (B018 маніфест, F401 тести)"}
  - {id: i18n-uk, status: PASS, msg: "тест повноти uk.po в кожному модулі; у UI латиниця лише в назвах ToDo/Odoo/CRM, прикладах адрес і Ctrl+V"}
  - {id: real-email, status: PASS, msg: "локальний SMTP-приймач отримав 4 листи; тема [ToDo-support][<uuid>] TDS/…"}
  - {id: ee, status: SKIP, msg: "Enterprise недоступна — не перевірено (лише тест прапорця)"}
data_sources: ["repo:odoo/odoo@19.0 a157617c", "repo:package/addons@9525c4a", "repo:package/config + package/demo/answers.yaml"]
memo: |
  Невпевнений: поведінка на живій Enterprise (вихідників EE немає); у td_home_menu розширення навбару реєструється з JS
  лише на CE — на EE шаблон не чіпається; кнопка td_support на діалогах помилок змінює лише слот footer web.ErrorDialog.
  Що змінилось: 2 нові модулі в package/addons/ (LGPL-3, з нуля; web_enterprise і web_responsive не використано).
  Канал (рішення AI, вето власника): лист через вихідний сервер на td_support.email; вебхук — каркас, вимкнений.
  Адресу підтримки не задано в модулі (не вигадував) — у демо support@example.com і локальний приймач.
  Де ризик: тексти ядра Odoo в діалозі помилки («Something went wrong…», «Odoo Server Error») не перекладені в uk самим
  Odoo — не наш модуль. Номери TDS/000xx у демо великі, бо послідовність не відкочується тестами.
  Що перевірити: скриншоти й відео в tests/reports/core-modules/; відкриті питання — tests/open-questions.md (3 рядки 2026-11-14).
observations: [observations/2026-11-14-core-modules-no-skill.md]
```

## Файли для власника (`tests/reports/core-modules/`)
| Файл | Що на ньому |
|---|---|
| `01-home-desktop.png`, `02-home-search.png` | головний екран після входу; пошук «вироб» |
| `07-home-phone.png` | головний екран на телефоні 390×844 |
| `03-support-dialog.png`, `04-support-sent.png`, `08-support-phone.png` | вікно звернення («Що буде надіслано»), сповіщення, телефон |
| `05-error-dialog.png`, `06-error-to-support.png` | помилка сервера з кнопкою; вікно з трасуванням |
| `09-email-request.png`, `10-email-error.png` | отримані листи (тема, тіло) |
| `11-video.mp4` | 24 с: вхід → пошук → застосунок → головний екран → звернення → помилка → надсилання |

Бази (`test-core-full`) у git не кладено.
