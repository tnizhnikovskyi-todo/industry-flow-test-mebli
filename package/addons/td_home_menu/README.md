# td_home_menu — головний екран застосунків (лише Community)

Загальний модуль збірок ToDo (без галузевого префікса). Ліцензія LGPL-3. Версія `19.0.1.0.1`.

## Що робить
- Головний екран: плитки кореневих меню з іконкою `web_icon`, пошук застосунку за назвою, перехід клавіатурою
  (стрілки, Enter — відкрити, Esc — очистити пошук). На телефоні (390×844) — сітка в 3 колонки, клавіатура
  екрана не з'являється, доки людина не торкнеться пошуку.
- Відкривається: після входу (коли в адресі немає дії) і кнопкою з плитками в навбарі (на телефоні — кнопка поруч із
  «бургером» поточного застосунку). Гаряча клавіша — та сама, що в стандарті (`h`).
- Підписи плиток переносяться лише між словами (`overflow-wrap: normal; word-break: normal; hyphens: auto`; мову
  сторінки `<html lang>` модуль ставить з мови користувача, бо `web.layout` бекенда її не задає). Довге однослівне ім'я
  (≥ 12 літер, напр. «Обслуговування») — менший шрифт (`captionClass`, ≥ 16 — ще менший), плитка — від 124 px (A-11-fix4).
- Іконки кореневих меню `td_*` — власні, у стилі стандартних `icon.svg` Odoo 19 (без плашки, пласкі фігури палітри
  #985184, #005E7A, #1AD3BB, #FBB945, #F86126, #FC868B), `static/description/icon.svg` 50×50 + `icon.png` 100×100;
  тест `tests/test_app_icons.py` перевіряє `web_icon` усіх кореневих меню `td_*` у базі.
- Якщо в базі встановлено `web_enterprise`, модуль нічого не змінює: розширення навбару не реєструється,
  після входу відкривається стандартний перший застосунок.

## Походження коду
Написано з нуля на OWL для цього пакета. Код `web_enterprise` (ліцензія OEEL) і OCA `web_responsive` (AGPL) не
використано й не відкривався. Залежність — лише `web` (CE, LGPL-3).

## Як влаштовано
| Частина | Файл |
|---|---|
| Прапорець «Community» у `session` (`td_home_menu_active` = немає `web_enterprise` у стані `installed`/`to upgrade`) | `models/ir_http.py` |
| Клієнтська дія `td_home_menu` (компонент екрана) | `static/src/home_menu/home_menu.{js,xml,scss}` |
| Кнопка в навбарі, відкриття після входу | `static/src/navbar/navbar_patch.js` |

Розширення шаблону навбару зареєстровано з JS (`registerTemplateExtension`) лише коли прапорець увімкнено. Так на
Enterprise шаблон навбару не змінюється взагалі: немає xpath, який міг би не знайти елемент у зміненому Enterprise
шаблоні й зламати весь інтерфейс.

## Звірка з вихідниками Odoo 19.0
Вихідники: `odoo/odoo`, гілка `19.0`, коміт `a157617c` (2026-11-14). Шляхи — від кореня репо Odoo.

| Твердження | Де в 19.0 |
|---|---|
| Навбар — компонент `NavBar`, шаблон `web.NavBar` | `addons/web/static/src/webclient/navbar/navbar.js:27-28` |
| Кнопка застосунків — підшаблон `web.NavBar.AppsMenu`: на телефоні `a.o_menu_toggle` (бічна панель), на десктопі `div.o_navbar_apps_menu` з випадним списком, інакше `div.mx-2` | `addons/web/static/src/webclient/navbar/navbar.xml:75`, `:77`, `:82`, `:100` |
| У `NavBar` є `actionService` | `addons/web/static/src/webclient/navbar/navbar.js:41` |
| Розширення шаблону з JS — `registerTemplateExtension(inheritFrom, url, templateString)`; саме його Odoo генерує для XML-розширень | `addons/web/static/src/core/templates.js:187`; `odoo/addons/base/models/assetsbundle.py:417` |
| Порожнє значення `<attribute>` прибирає атрибут (`t-else` → `t-elif`) | `addons/web/static/src/core/template_inheritance.js:230-236` |
| Без дії в адресі `WebClient` викликає `_loadDefaultApp()` (стандарт — перше кореневе меню) | `addons/web/static/src/webclient/webclient.js:138-143` |
| Клієнтська дія без `path` пишеться в адресу тегом і після перезавантаження знаходиться в реєстрі `actions` | `addons/web/static/src/webclient/actions/action_service.js:1817`, `:527` |
| Кореневі меню — `menuService.getApps()`; відкриття — `selectMenu(menu)` | `addons/web/static/src/webclient/menus/menu_service.js:70`, `:87` |
| `webIconData` — data-URI іконки або `/web/static/img/default_icon_app.png`; інакше `webIcon` = «клас,колір,фон» | `addons/web/models/ir_ui_menu.py:57-71`, `:83` |
| Нечіткий пошук — `fuzzyLookup(pattern, list, fn)` | `addons/web/static/src/core/utils/search.js:68` |
| `session_info()` розширюється через `super()` і стає `session` у JS | `addons/web/models/ir_http.py:84`; `addons/web/static/src/session.js:1`; приклад — `addons/web_tour/models/ir_http.py` |
| Шлях `apps` зайнятий дією модулів, тому власний `path` дії не задано | `odoo/addons/base/views/ir_module_views.xml:197` |

Enterprise (`web_enterprise`) вихідників у сесії немає: поведінку на EE перевірено лише тестом прапорця
(`tests/test_home_menu.py::test_inactive_with_enterprise`), не на живій EE — «не перевірено» до доступу до EE.

## Тести
- `tests/test_home_menu.py` — прапорець на CE увімкнено; з `web_enterprise` у стані `installed` вимкнено; тур
  `td_home_menu_tour`: після входу відкривається головний екран, пошук назви «Налаштування» (мовою користувача) лишає
  одну плитку, Enter відкриває застосунок, кнопка навбару повертає головний екран.
- `tests/test_i18n_po.py` — усі тексти модуля є в `i18n/td_home_menu.pot` і перекладені в `i18n/uk.po`.

Запуск: `tools/odoo/run_tests.sh <база test-*> td_home_menu`.
