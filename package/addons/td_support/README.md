# td_support — звернення в підтримку ToDo (Community і Enterprise)

Загальний модуль збірок ToDo (без галузевого префікса). Ліцензія LGPL-3. Версія `19.0.1.0.0`.
Залежності: `base_setup`, `mail` (обидва CE).

## Що робить
1. **Значок «Підтримка ToDo» у верхній панелі** відкриває вікно звернення: тема, опис, вкладення (файли або скриншот,
   вставлений Ctrl+V), контакт для відповіді (за замовчуванням — пошта або телефон користувача), згода. Розділ
   «Що буде надіслано» показує адресата, логін, сторінку, версію Odoo, ідентифікатор бази, перелік модулів `td_*`
   з версіями. Кнопка «Надіслати» активна лише після згоди. Посилання «Мої звернення» — історія користувача.
2. **Кнопка «Надіслати в підтримку ToDo» на діалогах помилок Odoo** (клієнтські, мережеві, серверні — усі діалоги на
   шаблоні `web.ErrorDialog`): те саме вікно з темою «Помилка: …» і розгорнутим трасуванням; людина бачить текст і
   підтверджує згоду. Кнопку бачать лише внутрішні користувачі.
3. **Запис `td.support.request`** (номер `TDS/00001`) зберігає звернення в базі: історія для користувача (власні) і для
   групи «Адміністратор підтримки» (усі; меню Налаштування → Підтримка ToDo).
4. **Надсилання.** Канал за замовчуванням — лист через вихідний поштовий сервер Odoo (черга `mail.mail`, запуск
   планувальника пошти одразу) на адресу з параметра `td_support.email`. Тема:
   `[ToDo-support][<uuid бази>] TDS/00001: <тема>` — за тегом intake (мітка Gmail) розпізнає звернення. Тіло — таблиця
   технічних даних, опис, модулі, трасування; вкладення — файли звернення; `Reply-To` — контакт, якщо це пошта.
   Опційний вебхук (каркас, вимкнено): POST JSON на `https://`-адресу з підписом
   `X-ToDo-Signature: sha256=<HMAC-SHA256 тіла секретом>`, тайм-аут 5 с.

Рішення про канал прийняв AI за дорученням (лист за замовчуванням, вебхук — каркас); власник продукту має право вето.

## Захист
- **Санітизація** (сервер, до запису й листа; `sanitize_text`): значення ключів `password/passwd/pwd`, `secret`,
  `token`, `api_key`, `session_id`, `csrf_token`, `cookie`, `authorization`, `private_key`, `signature` у формах
  `ключ=значення`, `ключ: значення`, `"ключ": "значення"`, `?ключ=значення` → `***`; рядки заголовків `Cookie:`,
  `Set-Cookie:`, `Authorization:`, `X-…-Token/Key:` → `***`; `Bearer/Basic <токен>` → `***`. Застосовується до теми,
  опису, контакту, адреси сторінки й трасування.
- **Розмір**: трасування й опис — до `td_support.max_text_chars` (20 000) символів, зберігаються початок і кінець;
  тема — 200; вкладень — до `td_support.max_attachments` (5), разом до `td_support.max_attachments_mb` (10 МБ).
- **Повторні надсилання**: не більше `td_support.rate_limit_per_hour` (5) звернень користувача за годину; те саме
  звернення (та сама тема й трасування) не приймається повторно протягом 10 хв.
- **Права**: створювати може будь-який внутрішній користувач (`base.group_user`; портал і гості — відмова), читати —
  лише власні; змінювати й видаляти — лише «Адміністратор підтримки» (`td_support.group_td_support_admin`; її має
  `base.group_system`). Технічні дані (логін, версія, модулі, uuid) рахує сервер, не браузер.

## Параметри (`ir.config_parameter`; перші чотири — у Налаштуваннях, блок «Підтримка ToDo»)
| Параметр | За замовчуванням | Призначення |
|---|---|---|
| `td_support.email` | — (не задано) | адреса підтримки; без неї звернення зберігається зі станом «Не надіслано» |
| `td_support.webhook_enabled` | вимкнено | вебхук |
| `td_support.webhook_url` | — | лише `https://` |
| `td_support.webhook_secret` | — | секрет HMAC (бачить лише адміністратор) |
| `td_support.rate_limit_per_hour` | 5 | ліміт звернень користувача |
| `td_support.max_text_chars` | 20000 | обрізання трасування й опису |
| `td_support.max_attachments` / `td_support.max_attachments_mb` | 5 / 10 | ліміти вкладень |

## Модель даних
| Модель / поле | Стандартний аналог | Чому не стандарт |
|---|---|---|
| `td.support.request` | `mail.mail` (лист у черзі) | звернення має жити в базі довше за лист (`mail.mail` після надсилання може видалятися), мати права «власні / усі», технічний контекст, згоду й стан каналів; лист — стандартний `mail.mail`, на нього посилається `mail_id` |
| `res.config.settings.td_support_email` | `ir.config_parameter` | це поле — лише показ параметра `td_support.email` у Налаштуваннях (`config_parameter=`), окремих даних немає |
| `res.config.settings.td_support_webhook_enabled` | `ir.config_parameter` | показ параметра `td_support.webhook_enabled` |
| `res.config.settings.td_support_webhook_url` | `ir.config_parameter` | показ параметра `td_support.webhook_url` |
| `res.config.settings.td_support_webhook_secret` | `ir.config_parameter` | показ параметра `td_support.webhook_secret` |

## Звірка з вихідниками Odoo 19.0
Вихідники: `odoo/odoo`, гілка `19.0`, коміт `a157617c` (2026-11-14). Шляхи — від кореня репо Odoo.

| Твердження | Де в 19.0 |
|---|---|
| Навбар показує всі записи реєстру `systray` (`{ Component }`, сортування `sequence`) | `addons/web/static/src/webclient/navbar/navbar.js:19`, `:107-112`; `navbar.xml:35`; приклад реєстрації — `addons/mail/static/src/discuss/call/common/call_menu.js:30` |
| Базовий діалог помилки — `ErrorDialog` (шаблон `web.ErrorDialog`); підкласи `ClientErrorDialog`, `NetworkErrorDialog`, `RPCErrorDialog` мають той самий шаблон і прототип | `addons/web/static/src/core/errors/error_dialogs.js:47-48`, `:89`, `:95`, `:107` |
| Пропси діалогу: `traceback`, `message`, `name`; `contextDetails` у `setup`; у `RPCErrorDialog` — `this.traceback` (з `data.debug` сервера) | `addons/web/static/src/core/errors/error_dialogs.js:15-28`, `:61`, `:111-114` |
| Кнопки — слот `footer` шаблону `web.ErrorDialog` | `addons/web/static/src/core/errors/error_dialogs.xml:53`, `:73` |
| Сервіс помилок відкриває ці діалоги через `dialog.add(...)` з `traceback` | `addons/web/static/src/core/errors/error_handlers.js:67`, `:159`, `:174` |
| `button.o-default-button:not(:only-child)` ховається — тому з «Закрити» знято цей клас, щоб кнопка лишилась | `addons/web/static/src/core/dialog/dialog.scss:17` |
| `user.isInternalUser`, `user.login` у JS | `addons/web/static/src/core/user.js:41`, `:162` |
| Версія сервера — `odoo.service.common.exp_version()['server_version']` (так само в `session_info`) | `addons/web/models/ir_http.py:87` |
| uuid бази — параметр `database.uuid` | `odoo/addons/base/models/ir_config_parameter.py:20` |
| `mail.mail` успадковує `mail.message` (`subject`, `attachment_ids`), має `email_to`, `body_html`, стан за замовчуванням `outgoing` | `addons/mail/models/mail_mail.py:31`, `:49`, `:64`, `:75`; `addons/mail/models/mail_message.py:91`, `:105` |
| Планувальник черги пошти — `mail.ir_cron_mail_scheduler_action`; позачерговий запуск — `ir.cron._trigger()` | `addons/mail/data/ir_cron_data.xml:4`; `odoo/addons/base/models/ir_cron.py:735` |
| Адреса відправника за замовчуванням — `ir.mail_server._get_default_from_address()` | `odoo/addons/base/models/ir_mail_server.py:641` |
| Внутрішній користувач — `res.users._is_internal()` | `odoo/addons/base/models/res_users.py:1165` |
| Групи 19.0 — через `res.groups.privilege` (`privilege_id`) | `odoo/addons/base/models/res_groups.py:36`; `odoo/addons/base/models/res_groups_privilege.py:4` |
| Блок налаштувань «Integrations» (`name="integration"`) — місце нового блока | `addons/base_setup/views/res_config_settings_views.xml:141` |
| `str2bool(s, default)` | `odoo/tools/misc.py:493` |

Enterprise: модуль не залежить від модулів EE; вихідників EE у сесії немає, тож на живій EE не перевірено (розширення
`web.ErrorDialog` торкається лише слоту `footer`).

## Тести
- `tests/test_support_request.py`: звернення створюється, лист у черзі (`outgoing`) з темою
  `[ToDo-support][<uuid>] TDS/…: …`, адресатом із параметра, вкладенням і `Reply-To`; трасування з паролем, токенами,
  cookie, Bearer, `api_key`, `csrf_token`, `access_token` очищене і в записі, і в листі; обрізання довгого тексту;
  ліміт за годину (окремо для кожного користувача); повтор того самого звернення; згода й тема обов'язкові; ліміти
  вкладень; права (власні / усі / портал — відмова; користувач не змінює й не видаляє); без адреси — стан
  «Не надіслано»; вебхук вимкнено за замовчуванням, увімкнений — один POST з підписом без секрету в тілі.
- `tests/test_support_tour.py`: тур `td_support_tour` — значок у верхній панелі, вікно, «Що буде надіслано» (версія 19.0),
  кнопка неактивна без згоди, надсилання, сповіщення з номером; лист у черзі.
- `tests/test_i18n_po.py`: усі тексти перекладено в `i18n/uk.po`.

Запуск: `tools/odoo/run_tests.sh <база test-*> td_support`.

## Відкриті питання (до власника)
- Реальна адреса підтримки для `td_support.email` (у модулі не задано — адресу не вигадано); налаштування фільтра
  мітки Gmail за тегом `[ToDo-support]`.
- Приймач вебхука (URL, секрет) — каркас вимкнено до рішення.
