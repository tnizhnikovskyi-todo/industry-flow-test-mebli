# Дефекти установки стенда
SHA стенда: b794c20 (`package/` = `1925fb8`)   Інстанс: demo-mebli-pkg-a   Профіль: package/demo/answers.yaml (A, ce)   Код повернення: A-14

## D-01 — модуль — **ЗАКРИТО** (A-11 спроба 6, `tests/reports/A-11-6.md`; `td_mebli_demo` 19.0.1.1.1; перевірено підйомом A-15 спроба 3, `tests/reports/A-15-3.md`)
- Місце: `package/addons/td_mebli_demo/showcase.py:225–227` (`_localize`, виклик із `seed_showcase`, `showcase.py:454`); крок up.sh «демо-документи (seed)» (код 50), після кроків 1–4 (модулі, конфіг A-12, шаблони A-13 — OK).
- Витяг з логу (`odoo-bin shell` < `package/demo/data/seed_demo.py`):
  ```
  File "/home/user/odoo19/delivery/td_mebli_demo/showcase.py", line 454, in seed_showcase
    _localize(env)
  File "/home/user/odoo19/delivery/td_mebli_demo/showcase.py", line 226, in _localize
    tax.with_context(lang='en_US').name = 'VAT 20%'
  File "/home/user/odoo19/src/addons/account/models/account_tax.py", line 249, in _constrains_name
    raise ValidationError(
  odoo.exceptions.ValidationError: Tax names must be unique!
  - VAT 20% in My Company
  ```
- Очікувалось / сталось: демо-шар має ставитися поверх налаштованої бази (модулі + конфіг A-12 + шаблони A-13); `_localize` перейменовує й переводить на 20 % **усі** податки зі ставкою ≠ 0, що розраховано на загальний план рахунків (еталонні демо-бази A-21 — без конфігу), а конфіг A-12 (`data/15_accounting.yaml`, план `ua_psbo`, VP-18) дає кілька податків — назви збігаються, seed падає (і перезаписав би ставки податків конфігу).
- Діагностика (scratch, без коміту): якщо перейменування податків пропустити, `seed_showcase` проходить до кінця на тій самій базі (124 замовлення, 110 MO, 49 закупівель, 123 задачі, 2209 партій) — інших дефектів демо-шару не виявлено.
- Проявляється на профілі: усі, де ставиться демо-шар (`answers.yaml` A; alt-2/alt-3 — B, перевірено лише з `--no-demo`); light (alt-1) — демо-шар не ставиться (залежність `td_mebli_bas`).

# Дефекти сценаріїв A-16 (прогін 1, 2026-11-14)
Стенд: `demo-mebli-pkg-a` (ce, `answers.yaml` B-демо) зі знімка A-15 спроба 3; гілка `flow/A-12-2-test` @ `c4cf89d`. Таблиця сценаріїв —
`package/demo/scenarios.md`. Код модулів не змінювався: нижче — місце, витяг, пропозиція. Повернення: **A-11** (D-02…D-09, D-11…D-15), **A-12** (D-10).

## D-02 — модуль — критичний — A-11: нове замовлення не зберігається з форми — **закрито (A-11-7, тест `td_mebli_install/tests/test_a11_7.py::test_d02_new_order_saved_from_the_full_form`, `td_mebli_sale/tests/test_a11_7.py::test_d02_*`, тур `td_mebli_sale/tests/test_configurator_tour.py` — менеджер salon, uk_UA, повний профіль A)**
- Виправлення A-11-7: `td_stage` у формі — `readonly="1"`; `_inverse_td_stage` нічого не робить, якщо значення = похідному (`_td_stage_value`, розширено в `td_mebli_install`).
- Місце: `package/addons/td_mebli_install/views/payment_views.xml:11` (`<field name="td_stage" invisible="1"/>` у формі `sale.order`, без `readonly`)
  + `package/addons/td_mebli_sale/models/sale_order.py:16-20` (`td_stage` — compute + `inverse`, `readonly=False`) і `:56-69` (`_inverse_td_stage`).
- Відтворення (менеджер `salon`, UI): Продажі → «Новий» → клієнт → «Додати товар» → «Зберегти» → «Недійсна операція: Етап рахується з документів;
  запуск виробництва — лише начальник виробництва», запис не створено. Під admin (тур) — «The stage follows the production: only moving a waiting order
  to «In production» is possible.» (лог `odoo.http` WARNING на `sale.order/web_save`).
- Причина: поле в арху форми не readonly → клієнт передає `td_stage='quote'` у `web_save` нового запису → `inverse` відкидає будь-яке значення, крім
  `progress`. На мінімальній базі (без `td_mebli_install`) поля у формі немає — тому тур там проходить.
- Пропозиція: `readonly="1"` для `td_stage` у `payment_views.xml:11` (і перевірити інші арх-и з `td_stage`, напр. `td_mebli_dashboard/views/sale_order_views.xml:17`);
  у `_inverse_td_stage` — нічого не робити для записів, де нове значення = обчисленому (створення, збереження без перетягування).
- Блокує: T-01 крок 0 (S-02), тур конфігуратора, будь-яке створення пропозиції менеджером у UI.

## D-03 — модуль — критичний — A-11: форма замір-листа не відкривається (OwlError) — **закрито (A-11-7, тест `td_mebli_measure/tests/test_form_roles.py` — HttpCase-тур відкриття форми під 5 ролями + перевірка, що `options` — літерали)**
- Виправлення A-11-7: звірено: Odoo 19 `web/static/src/views/fields/field.js:270` — `fieldInfo.options = evaluateExpr(value)` без запису; динамічний `no_open` замінено двома копіями поля (`invisible` за `td_can_link`, у копії без права — `readonly` + `no_open: True`).
- Місце: `package/addons/td_mebli_measure/views/measure_views.xml:21-22` — `options="{'no_open': not td_can_link}"` (у Odoo 19 `options` обчислюється
  статично, без значень запису).
- Витяг (консоль, усі ролі — замірник, менеджер, технолог, фінансист, власник): `EvalError: Can not evaluate python expression: ({'no_open': not td_can_link})
  Error: Name 'td_can_link' is not defined` → діалог «От халепа!».
- Пропозиція: прибрати динамічний `no_open` (лишити `readonly="not td_can_link"`) або `options="{'no_open': True}"` для обох полів.
- Блокує: AC-005, AC-007, AC-008 (UI замірника), AC-006 (частина), смарт-кнопку «Заміри» на замовленні.

## D-04 — модуль — високий — A-11: зміна розмірів у рядку не змінює ціну (AC-015) — **закрито (A-11-7, тест `td_mebli_sale/tests/test_a11_7.py::test_d04_*` (Form) і тур конфігуратора — ширина в рядку 1000→1200, ціна ×1,2)**
- Виправлення A-11-7: `_get_display_price` бере `td_width/td_height` рядка; inverse `_inverse_td_dims` записує розмір у значення конфігуратора й опис рядка.
- Місце: `package/addons/td_mebli_sale/models/sale_order_line.py:14-16` (`td_width/height/depth` — compute з власних значень атрибутів, `readonly=False`, без inverse),
  `:87-90` (`td_size_factor` від `td_width/td_height`), `:107-115` (`_get_display_price` множить на коефіцієнт із `_td_get_dims()` — власних значень атрибутів).
- Відтворення: менеджер у пропозиції змінює «Ширина, мм» рядка 1600→1800 і зберігає: коефіцієнт 1→1,125, ціна 21 000 → 21 000.
- Пропозиція: inverse `td_width/td_height/td_depth` → записувати власні значення атрибутів рядка (`product_custom_attribute_value_ids`), або в
  `_get_display_price` брати `self.td_width/td_height`; альтернатива — зробити колонки readonly (зміна лише через конфігуратор) і виправити AC-015 у ТР.

## D-05 — модуль — середній — A-11: суми етапів оплати не видно у формі (AC-019) — **закрито (A-11-7, за текстом AC-019; тести `td_mebli_sale/tests/test_a11_7.py::test_d05_milestones_in_the_form`, `td_mebli_install/tests/test_a11_7.py::test_d05_due_and_received_in_the_quotation_form`)**
- Виправлення A-11-7: під умовами оплати — таблиця етапів (`td_pay_schedule_html`), «Перед монтажем потрібно» і «Отримано» без банера, уже в пропозиції; «бракує» рахується лише після підтвердження.
- Місце: `package/addons/td_mebli_install/views/payment_views.xml:9-16` — «Перед монтажем потрібно» / «Отримано» лише всередині банера-попередження
  (`invisible="td_pay_ok or state != 'sale' or td_stage in ('closed', 'progress', 'confirmed')"`).
- Факт: S00023 з умовами 50/40/10 після підтвердження — сум етапів і «Отримано» у формі немає; у договорі етапи є.
- Пропозиція: окрема група полів (`td_pay_before_install`, `td_pay_received`, суми етапів) у формі замовлення при умовах з етапами, незалежно від банера.

## D-06 — модуль (права) — високий — A-11: дії ролей без потрібних прав моделі — **закрито (A-11-7, тести `td_mebli_cutting/tests/test_distributor.py::test_d06_technologist_sends_to_distributor_without_purchase_rights` (перевірка права на завдання → закупівля послуги `sudo`, автор/відповідальний — технолог, `return_date` `compute_sudo`), `td_mebli_purchase/tests/test_price_import.py::test_d06_buyer_imports_the_price_list` (ACL `product.supplierinfo` RWC для `purchase.group_purchase_user`, запис у чаттер постачальника — `sudo` з автором-закупівельником))**
- (а) Технолог «Передати дистриб'ютору» (AC-026): `package/addons/td_mebli_cutting/models/distributor.py:63` — `self.env['purchase.order'].create(...)` з правами
  користувача; технолог за `package/tr/security.md:12` прав закупівлі не має → AccessError «Ви не можете створювати записи Purchase Order».
- (б) Закупівельник (`store`, `purchase.group_purchase_user`) імпорт прайсу (AC-087): `package/addons/td_mebli_purchase/wizard/price_import.py` `action_import` (`:165`)
  створює `product.supplierinfo`; в Odoo 19 create — лише `purchase.group_purchase_manager` / `product.group_product_manager` → AccessError.
- Пропозиція: (а) `sudo()` на створення закупівлі послуги після явної перевірки групи технолога (і `message_post` автора); (б) ACL `product.supplierinfo`
  (create/write) для `purchase.group_purchase_user` у `td_mebli_purchase/security/ir.model.access.csv` або `sudo()` після перевірки групи закупівельника.

## D-07 — модуль (меню/права) — середній — A-11: «Оновити ціни за курсом» видно всім, дія — лише фінансисту — **закрито (A-11-7, тест `td_mebli_ua/tests/test_ua.py::test_ac_037_menu_behind_the_feature_group` — видимість меню під фінансистом/менеджером/працівником, з функцією і без)**
- Виправлення A-11-7: меню — `groups` = `group_finance` (стару `group_feature_nbu` знято `-` при оновленні); функцію «nbu» перевіряє `ir.ui.menu._visible_menu_ids` (`td_mebli_ua/models/ir_ui_menu.py`).
- Місце: `package/addons/td_mebli_ua/views/views.xml:22-23` — меню з `groups="td_mebli_base.group_feature_nbu"` (функція коробки, неявна для всіх), дія — `group_finance`.
- Факт: менеджер, технолог, начальник, комірник, замірник, бригадир, планшет бачать пункт у «Продажі» → «У вас недостатньо прав, щоб запустити цю дію»;
  через нього ж замірник/бригадир/планшет бачать застосунок «Продажі».
- Пропозиція: `groups="td_mebli_base.group_finance"` на меню (видимість функції — через батьківське меню з `group_feature_nbu` або перевірку в дії).

## D-08 — модуль (демо-дані) — середній — A-11 (узгодити з A-15 `plan.md` §2): групи демо-ролей ширші за план — **закрито (A-11-7: замірник — лише `group_td_mebli_measurer`, бригадир — `project.group_project_user` + нова група «Сервіс» `td_mebli_claim.group_service` (implied `stock.group_stock_user`, SPEC tr/security.md §1), монтажник — `project.group_project_user`; «Повторне виготовлення» сервісом без прав виробництва — перевірка права на рекламацію → МО `sudo`; тести `td_mebli_demo/tests/test_scenario.py::TestDemoRoles`, `td_mebli_claim/tests/test_claim.py::TestServiceRole`; на базі демо: measure/fitter/fitter2 без групи продажів)**
- Місце: `package/addons/td_mebli_demo/showcase.py:49-53` — `measure`, `fitter`, `fitter2` отримують `sales_team.group_sale_salesman_all_leads`;
  `package/demo/plan.md` §2: замірник — лише `group_td_mebli_measurer`, бригадир — `project.group_project_user`.
- Факт (AC-006 FAIL): замірник бачить CRM і «Продажі» та читає замовлення з сумою. Окремої демо-ролі «Сервіс» (`group_service`, `stock_user` + `repair`)
  немає — T-06 виконано від `store`, бригадир доступу до рекламацій не має.
- Пропозиція: групи демо-ролей за `plan.md` §2 / `tr/security.md` §1 (замірник без продажів); додати роль сервісу або дати бригадиру `group_service`.

## D-09 — модуль (демо-дані) — середній — A-11: у демо-працівників і частини контрагентів немає коду BAS — **закрито (A-11-7, `td_mebli_demo/full.py` `_bas_codes`: коди BAS усім працівникам, контрагентам рахунків і товарам рахунків; один покупець без коду навмисно — AC-040. Перевірено повтором наповнення демо (`test-mebli-a117t-demo`): працівників без коду 0, «Передати в BAS» 50 підтверджених нарахувань — пакет `sent`, помилок 0)**
- Місце: `package/addons/td_mebli_demo` (seed) — `hr.employee.td_bas_code`, `res.partner.td_bas_code` (`td_mebli_bas/models/codes.py:9-21`) не заповнені.
- Факт (AC-109): «Передати в BAS» для 50 підтверджених нарахувань — пакет створено, усі 50 — `bas_state = error` «The employee … has no BAS code»;
  рахунки 8 контрагентів — «Контрагент … не має коду BAS». Перевірка коду працює (AC-040 PASS), але демо-сценарій T-07 не проходить.
- Пропозиція: seed кодів BAS для демо-працівників і контрагентів (синтетичні, як інші дані демо).

## D-10 — конфіг (дані) — середній — A-12: немає виключень атрибутів (AC-011) — **закрито (A-12-5 + A-11-7: виключення — дані виробу, не конфіг (`package/config/CONFIG.md` спроба 5); демо-каталог — «ЛДСП Антрацит — лише кромка 2 мм» для шафи-купе й кухонного модуля, `td_mebli_demo/hooks.py` `EXCLUSIONS`, тест `test_d10_exclusions_of_the_configurator`; на базі демо 2 записи; шаблон A-13 — `tests/open-questions.md`)**
- Факт: `product.template.attribute.exclusion` у базі — 0 записів; конфігуратор «Шафа-купе 2-дверна» пропонує всі декори/кромки без обмежень.
  `package/addons/AC-COVERAGE.md:20`: «Виключення атрибутів — дані A-12».
- Пропозиція: дані виключень «декор X — лише кромка X» у конфіг-пакеті A-12 (`package/config/data/`) для параметричних виробів демо/шаблонів.

## D-11 — модуль — низький — A-11: комплектувальний лист не можна сформувати в UI (AC-091) — **закрито (A-11-7: кнопка «Сформувати комплектувальний лист» у шапці підтвердженого замовлення і «Комплектувальний лист» у відвантаженні для `stock.group_stock_user`; тест `td_mebli_shop/tests/test_d11_kit_button.py` — кнопка у view під роллю комірника (get_views), Form замовлення, формування з замовлення й відвантаження без перебудови запакованого)**
- Місце: `package/addons/td_mebli_shop/models/kit.py:73` `action_td_build_kit` — викликається лише з `td_mebli_demo/full.py:234,271`; кнопки у
  `td_mebli_shop/views/kit_views.xml:46-65` немає (є лише «Сканувати етикетки» й смарт-кнопка, коли лист уже є).
- Пропозиція: кнопка «Сформувати комплектувальний лист» у шапці замовлення/відвантаження для `stock.group_stock_user`.

## D-12 — модуль — середній — A-11: немає вкладки «Собівартість» на формі пропозиції (AC-017) — **закрито (A-11-7, за текстом AC-017; тест `td_mebli_sale/tests/test_a11_7.py::test_d12_cost_tab`)**
- Виправлення A-11-7: вкладка «Собівартість» (`td_cost_plan`, групи MARGIN_GROUPS — AC-018): рядки з плановими матеріалами, операціями, собівартістю, маржею; маржа й маржа % замовлення.
- Факт: фінансист/керівник продажу на формі пропозиції бачать маржу й маржу %, але не планові матеріали й операції рядка; вкладки «Собівартість» немає
  (поля `td_planned_material_cost/_operation_cost` — лише у звіті `td_mebli_sale/views/order_cost_report_views.xml`).
- Пропозиція: сторінка «Собівартість» у формі `sale.order` (`td_mebli_sale/views/sale_order_views.xml`) з `td_planned_*`, `purchase_price`, `margin` рядків,
  `groups` = MARGIN_GROUPS.

## D-13 — модуль (i18n) — низький — A-11: англійські тексти в uk_UA (AC-N.01) — **група T закрито (A-11-7, модулі cutting/purchase/shop/mrp/base/bas/dashboard/notify/claim/migration/attendance/maint/multico): активність «Прогноз пізніший…» — мовою менеджера (крон працював en_US), «Новий» у новому завданні розкрою, переклади, яких не було в `.pot` (Odoo відкидає їх як застарілі), доповнено; тести `td_mebli_notify/tests/test_notify.py::test_d13_activity_in_the_language_of_the_salesperson`, `td_mebli_cutting/tests/test_access.py::test_d13_new_job_name_in_ukrainian`, `td_mebli_base/tests/test_i18n_po.py`)**
- Група S (A-11-7, модулі sale/measure/install/ua/cost) — **закрито у своїх модулях** (тести `td_mebli_sale/tests/test_a11_7.py::test_d13_axis_in_the_language_of_the_user`, `td_mebli_install/tests/test_a11_7.py::test_d13_act_in_ukrainian`): вісь у помилці розміру — перекладений підпис `td_dimension`; чек-лист акта, статуси «Чернетка/Підписано» і заголовок акта в uk_UA вже перекладені в `uk.po` (тест на чистій базі з uk_UA — PASS; англійський текст на стенді — ймовірно акти, створені демо-шаром без мови, або переклади без `--i18n-overwrite` — перевірити на A-15); решта пунктів (bas, notify, cutting, purchase, кіоск) — інші модулі.
- Чек-лист акта за замовчуванням англійською (`td_mebli_install/models/act.py:25`, видно у формі й PDF акта); заголовки форм «Installation Act»
  (`td_mebli_install/views/act_views.xml:7`), «Exchange Batch» (`td_mebli_bas/views/bas_views.xml:78`), «Cutting Job», статуси акта «Draft/Signed»;
  активність «Forecast later than promised by N days» (`td_mebli_notify/models/forecast_activity.py:40`); вісь у помилці «width 2600 мм поза межами»
  (`td_mebli_sale/models/sale_order_line.py:73,80` — `axis=axis` без перекладу); підказка аналога «… 12 free».
- Пропозиція: доповнити `i18n/uk.po` модулів; чек-лист — перекладним полем/даними; вісь — перекладені підписи; тур A-16 з перевіркою латиниці.

## D-14 — модуль (друк) — низький — A-11: PDF із запасним шрифтом (AC-N.06) — **закрито (A-11-7: шапка, підвал і адреса `web.external_layout` — поза `.page`; шрифт пакета тепер на весь аркуш звітів `td_mebli_*` через `body[data-report-id^="td_mebli_"]` (`web.minimal_layout`), клас `td_mebli_report` — на етикетки, лист передачі й комплектувальний лист; тести `td_mebli_base/tests/test_report_font.py::test_d14_header_footer_and_address_of_a_package_report` (wkhtmltopdf + pdffonts: 0 шрифтів, контроль стандартного звіту — запасний), `td_mebli_shop/tests/test_kit_report.py::test_d14_*`)**
- Факт (`pdffonts`): договір, акт монтажу, етикетки деталей, комплектувальний лист — вбудовано `DejaVuSerif`, `DejaVuSerif-Bold`.
  Етикетки й лист без класу `td_mebli_report` (`td_mebli_shop/report/label_report.xml:29`, `kit_report.xml:22`); у договорі й акті клас є, але
  частина тексту (ймовірно шапка/підвал `external_layout`) іде запасним шрифтом.
- Пропозиція: клас `td_mebli_report` на кореневий елемент етикеток і листа; застосувати шрифт пакета й до шапки/підвалу звітів пакета.

## D-15 — тест — низький — A-11: тур конфігуратора залежить від стартового меню й мови — **закрито (A-11-7, тур `td_mebli_sale_configurator_tour` — PASS на базі повного профілю A, uk_UA, користувач — менеджер salon)**
- Виправлення A-11-7: тур стартує з `/odoo/action-sale.action_quotations_with_onboarding`, селектори за полями/класами; меню «Замір-листи» — `sequence` 30 (після «Замовлень»).
- Місце: `package/addons/td_mebli_sale/tests/test_configurator_tour.py:10` (`start_tour('/odoo', …, login='admin')`) і
  `package/addons/td_mebli_sale/static/tests/tours/configurator_dimensions_tour.js:8-10` (`goToAppSteps('sale.sale_menu_root')` + `createNewSalesOrder`).
- Причина: на повному профілі «Продажі» відкривають «Замір-листи» (`td_mebli_measure/views/measure_views.xml:178-179`, `sequence="3"`), мова admin — uk_UA,
  а кроки стандарту шукають `.o_sale_order` і англійський текст.
- Пропозиція: тур стартує з `/odoo/action-sale.action_quotations_with_onboarding`; у `setUpClass` тесту — `lang='en_US'` для admin (або тур на селекторах
  без тексту); у пакеті — `sequence` меню замірів ≥ 30 (після «Замовлення»), якщо стартовий екран «Продажів» має лишитися стандартним.
