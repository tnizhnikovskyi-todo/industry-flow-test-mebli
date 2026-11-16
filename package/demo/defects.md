# Дефекти установки стенда

> A-16b-6 (2026-11-16): обмін з BAS/BAF **виключено рішенням власника 2026-11-16** — `td_mebli_bas`, `td_mebli_attendance` з пакета видалено (A-11-fix6).
> Згадки BAS у записах нижче (D-09, D-13, D-16, D-22 тощо) — історичний журнал закритих дефектів, не склад збірки; D-22 закрито як неактуальний.

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

# Перевірка закриття і нові дефекти — A-16 спроба 2 (2026-11-14)
Стенд: `demo-mebli-pkg-a` перебудовано (A-15 спроба 4, гілка `flow/A-12-2-test` @ `d2ec5df`, `answers.yaml` B-демо, ce). Таблиця — `package/demo/scenarios.md`
(колонка «Спроба 2»). Код модулів не змінювався.

Закриття на стенді: D-02 (нова пропозиція з форми зберігається, UI), D-03 (форма замір-листа — замірник і смарт-кнопка «Заміри» менеджера, без OwlError),
D-04 (ширина 1600→1800 — ціна 21 000→23 625), D-05 (етапи 50/40/10, «До сплати до монтажу», «Отримано» у формі), D-06 (технолог → закупівля порізки;
закупівельник — імпорт прайсу), D-07 / D-08 (замірник без «Продажів», читання замовлення — AccessError), D-09 («Передати в BAS» 50 — `bas_state` sent 50),
D-10 (виключення «ЛДСП Антрацит» → «ПВХ 0,4 мм» позначено недоступним у діалозі конфігуратора), D-11 (кнопка комірника — 9 рядків листа, 3 місця;
кнопка у відвантаженні), D-12 (вкладка собівартості — є, підпис англійською → D-16), D-15 (тур конфігуратора — 0 failed) — **PASS**.
D-13 — перелічені в дефекті тексти перекладено (у обході меню їх немає), але нові підписи A-11-7 — англійською (**D-16**). D-14 — шрифт пакета
працює лише коли `report.url` = адреса стенда (**D-17**).

## D-16 — модуль (i18n) — низький — A-11: нові підписи A-11-7 англійською в uk_UA (AC-N.01) — **закрито (A-11-8: .pot усіх td_mebli_* перегенеровано експортом з бази, uk.po зведено — кожен msgid перекладено; тест `td_mebli_base/tests/test_i18n_po.py` — усі встановлені модулі; перевірено A-16 спроба 3: «Собівартість», «Графік оплат»; залишок — повідомлення чату seed-а «BAS Exchange Batch створено», низький, відкрито)**
- Місце: `package/addons/td_mebli_sale/views/sale_order_views.xml:85` — вкладка `string="Cost of the Order"` (D-12); `td_mebli_sale/models/payment_term.py:28-29` —
  поля «Payment by Milestones», «Payment Schedule» (D-05). Переклади є в `td_mebli_sale/i18n/uk.po` (кінець файлу: «Собівартість», «Графік оплат»,
  «Оплата етапами»), у `td_mebli_sale/i18n/td_mebli_sale.pot` цих рядків немає.
- Факт (стенд після `up.sh` з `--i18n-overwrite`): `ir_ui_view` `td_mebli_sale.view_order_form_td_mebli` — у `arch_db->'uk_UA'` «Cost of the Order»
  (так само «Margin of the Order»); `ir_model_fields.field_description` uk_UA для `td_pay_schedule_html`, `td_pay_has_milestones` — порожній. Обхід меню:
  «Cost of the Order» (фінансист, власник), «Payment Schedule» (технолог, начальник, фінансист).
- Ймовірна причина: та сама, що описано в D-13 групи T — рядки є в `uk.po`, але не в `.pot` модуля (група S доповнила лише `uk.po`). Не перевірялось.
- Пропозиція: доповнити `td_mebli_sale.pot` (і перевірити інші модулі групи S: measure, install, ua) і тест на чистій базі з uk_UA, що читає ці підписи з БД.
- Дрібне, демо-шар: повідомлення в чаті пакета BAS «BAS Exchange Batch створено» (запис створено seed-ом без мови користувача).

## D-17 — стенд (конфіг) — середній — A-15 (за потреби A-11): `report.url` стенда не збігається з адресою сервера — PDF без стилів, запасний шрифт (AC-N.06) — **закрито (A-11-8: `td_mebli_demo/wave2.py` `_set_report_url` — `DEMO_REPORT_URL` або порожній → web.base.url, тест `td_mebli_demo/tests/test_report_url.py`; up.sh OK/WARN, README «PDF (D-17)»; A-15 спроба 5 з `DEMO_REPORT_URL=http://127.0.0.1:8079`; A-16 спроба 3: DejaVu у PDF немає)**
- Місце: `package/addons/td_mebli_demo/wave2.py:324` — `report.url` = `DEMO_REPORT_URL` або `http://127.0.0.1:8072`; `package/demo/up.sh` змінну не задає;
  README стенда: `serve.sh <instance> <порт>` — порт довільний; наряд A-16 — порт 8079.
- Факт: стенд як є — договір, акт, етикетки МО, комплектувальний лист: `pdffonts` — DejaVuSerif / DejaVuSerif-Bold (wkhtmltopdf не дістає стилі й шрифти з 8072).
  Той самий стенд з `report.url = http://127.0.0.1:8079`: акт і етикетки — без вбудованих шрифтів (як у тесті D-14), договір і лист — Inter-Regular/-Bold,
  DejaVu немає.
- Пропозиція: `up.sh` задає `DEMO_REPORT_URL` (адреса/порт стенда, параметр) і README фіксує порт сервера, або `serve.sh`/README — крок «report.url = адреса сервера»;
  на хостингу — `report.url` у конфігу сервера (`package/tr/nfr.md:38`). Окремо (A-11, за бажанням): договір і лист вбудовують Inter (шрифт макета), а не шрифт пакета — кирилиця є, не запасний шрифт.

## A-16-4 (2026-11-15) — стенд A-15-full `6b81620`: нових дефектів немає
Повтор турів T-01…T-13, тур конфігуратора A-15 і нові сценарії T-14 (`td_home_menu`), T-15 (`td_support`), T-16 (`td_knowledge`, `td_mebli_knowledge`):
FAIL 0 (`scenarios.md` «Спроба 4»). Повернення на A-14 немає. Дефект A-14-5 F-38 (прив'язка статей до екранів) закрито до стенда (A-11-fix2).


## D-18 — стенд (демо-дані) — низький — A-15: дві групи дільниць з однаковими назвами на стенді — **закрито (A-11-fix3 `ba0aff3`, стенд A-15-full-2 `15dbd6f`)**
Знайдено під час зйомки A-16b на `demo-mebli-pkg-a` @ `6b81620`: шаблони A-13 (`td_md.mrp_workcenter_cutting/edging/drilling/assembly` — «Розкрій»,
«Кромкування», «Присадка», «Збирання») і демо-шар `td_mebli_demo` (`wc_cut/edge/drill/asm` — «Розкрій», «Крайкування», «Присадка», «Складання»)
створюють 8 активних дільниць; у «Планшет цеху», «Завантаження дільниць» і «Робочі центри» «Розкрій» і «Присадка» видно двічі (перша група порожня).
Сценарії не блокує (кроки SC-03 виконуються; інструкція описує дільниці демо-шару), тому SC-03 у посібнику — «готово». Маршрут: A-15 (demo-base-builder:
демо-шар бере дільниці шаблонів A-13 або архівує їх), за потреби A-13 (узгодити назви «Кромкування/Крайкування», «Збирання/Складання»). Знімки
`img/nachalnyk-vyrobnytstva/SC-03-2.png`, `SC-03-4.png` показують дубль — після виправлення перезняти (A-16b refresh).
Перевірка 2026-11-15 (аудит прав ролей, стенд `demo-mebli-pkg-a` зі знімка, `faa25b7`): причину підтверджено — 8 активних дільниць: `td_md.mrp_workcenter_cutting/edging/drilling/assembly`
(id 1–4; `package/master-data/09_mrp.workcenter.csv:2-5`, імпорт `package/demo/up.sh:59`) мають лише операції шаблону `12_mrp.routing.workcenter.csv` (5) і 0 робочих завдань;
`td_mebli_demo.wc_cut/edge/drill/asm` (id 5–8; `td_mebli_demo/data/workcenter_data.xml:3…`, операції `data/product_data.xml:54…180`) — 127 операцій і 110 робочих завдань кожна.
Місце виправлення — демо-шар `td_mebli_demo` (A-11 модуль / A-15 підйом): операції демо-каталогу на дільниці шаблонів A-13 (`td_md.*`), коли вони є, або архівувати порожні
дільниці шаблонів після наповнення; узгодження назв «Кромкування/Крайкування», «Збирання/Складання» — A-13.
Закриття (A-15-full-2, 2026-11-15): `td_mebli_demo` 19.0.1.1.4 `pre_init_hook` переймає `td_md.mrp_workcenter_*` (AI-28) — на стенді 4 активні дільниці (Розкрій, Крайкування, Присадка, Складання; по 110 робочих завдань), smoke `verify_demo.py` перевіряє відсутність дублів. Назви A-13 у CSV не змінено (вибір термінів — A-13). Знімки `SC-03-2.png`, `SC-03-4.png` — перезняти (A-16b refresh).

## Аудит прав ролей (A-16b, 2026-11-15) — стенд `demo-mebli-pkg-a` зі знімка, `faa25b7`
Перевірено під кожною роллю: Playwright (Chromium, uk-UA, Europe/Kyiv) — меню (`/web/webclient/load_menus`), форми й кнопки; XML-RPC під тією ж роллю —
`check_access_rights` і виклик дії. Дії зі зміною даних (підтвердження нарахування, «Створити пропозицію») — потім стенд відновлено зі знімка (`tools/odoo/restore.sh`).
Не дефекти (за SPEC — лише текст інструкції): fin не бачить «Скасувати підтверджені» нарахування (кнопка `td_mebli_install/views/accrual_views.xml:13-14`,
`CANCEL_GROUPS` `models/accrual.py:11`; виклик `action_td_cancel` — «Підтверджене нарахування скасовує лише керівник.», майстер `td.mebli.accrual.cancel` —
«Ви не можете створювати записи 'Cancel Confirmed Accruals'…») — за AC-106 і `tr/security.md` §3 підтверджене скасовує лише керівник; група «Сервіс» у демо — лише
fitter (`td_mebli_demo/showcase.py:52-53`), не store — так за ROLE-10; store без меню «Продажі» і без смарт-кнопки замовлення на доставці (ROLE-05 без групи продажу,
SPEC рядок 50), «Комплектувальний лист» на доставці є (`td_mebli_shop/views/kit_views.xml:79`). Попутно (низький, i18n, D-16): назва моделі майстра «Cancel Confirmed
Accruals» англійською в повідомленні про доступ.

## D-19 — модуль (меню/права) — середній — A-11: менеджер салону не відкриває «Календар монтажів» і не планує виїзд (AC-044, UC-01 крок 11) — **закрито (A-11-fix3 `ba0aff3`, перевірено A-16-5 на стенді `15dbd6f`)**
Під salon (`sales_team.group_sale_salesman`, як ROLE-02 у SPEC рядок 46) меню «Проєкт» → «Монтаж» → «Календар монтажів» немає: батьківське меню
`td_mebli_install/views/act_views.xml:140` — під `project.menu_main_pm` (groups `project.group_project_manager,group_project_user`). Пряма адреса дії
`td_mebli_install_calendar_action` відкриває календар (читання задач є), але змінити дату виїзду не можна: `project.task.write` —
«Sorry, Олена Мартинюк (id=5) doesn't have 'писати' access to: - Завдання (project.task)». Іншого шляху немає: на формі замовлення смарт-кнопка задач
`sale_project` — `groups="project.group_project_user"`, кнопок пакета для виїзду на замовленні немає (кнопки «Створити рахунок, Надіслати, Попередній перегляд,
Скасувати, Створити зміну»). За SPEC менеджер «відкриває календар монтажів» (AC-044) і «планує доставку й монтаж — задача-виїзд» (UC-01 крок 11).
Маршрут: A-11 (`td_mebli_install`): меню «Календар монтажів» для `sales_team.group_sale_salesman` (напр. у «Продажі»), смарт-кнопка «Виїзд» на замовленні
і право запису дати/бригади задач-виїздів своїх замовлень (`ir.rule` за `sale_order_id.user_id`), або рішення A-08 дати ROLE-02 `project.group_project_user`
(тоді — демо `td_mebli_demo/showcase.py:33-35`). Тест — під менеджером: меню видно, дата виїзду змінюється.

## D-20 — модуль (права) — середній — A-11: технолог не веде «Правила деталей» і не бачить «Шаблони імпорту» в меню (SPEC `tr/security.md` §1–2) — **закрито (A-11-fix3 `ba0aff3`, перевірено A-16-5 на стенді `15dbd6f`)**
Під tech (`mrp.group_mrp_user`, `stock.group_stock_user`, `sale_salesman_all_leads`) у «Виробництво» немає «Налаштування» (меню ядра `mrp.menu_mrp_configuration`
— `groups="group_mrp_manager"`), отже немає «Правила деталей» (`td_mebli_mrp/views/part_rule_views.xml:48-49`, ще й `groups="mrp.group_mrp_manager"`) і
«Шаблони імпорту» (`td_mebli_mrp/wizard/spec_import_views.xml:101-102`, groups `mrp_user`, але під «Налаштуванням»). Пряма адреса дії правил — список лише
для читання (без «Новий»); `td.mebli.part.rule.write` — «Ви не можете змінити записи 'Правило деталі виробу' (td.mebli.part.rule). Ця операція доступна
наступним групам: - Виробництво/Адміністратор» (`td_mebli_mrp/security/ir.model.access.csv:2-3`: `mrp_user` — 1,0,0,0). Шаблони імпорту за прямою адресою — «Новий» є
(RWCD для `mrp_user`, рядок 10). За SPEC технолог — RWCD на `td.mebli.part.rule` і `td.mebli.import.template` (`tr/security.md` §2), група
`td_mebli_base.group_technologist` (§1; ROLE-01 — SPEC рядок 48) — у коді її немає. Маршрут: A-11 (`td_mebli_base`/`td_mebli_mrp`): група «Меблі: Технолог»
(implied `mrp_user`, `stock_user`) з RWCD на правила деталей і шаблони, меню обох поза «Налаштуванням» (або з групою технолога); демо — tech у групі технолога
(`td_mebli_demo/showcase.py:36-37`, A-11). Тест — під технологом: меню видно, правило створюється.

## D-21 — модуль (права) — високий — A-11: сервіс не створює пропозицію платного ремонту (AC-112, T-06) — **закрито (A-11-fix3 `ba0aff3`, перевірено A-16-5 на стенді `15dbd6f`)**
Рекламація (Ремонти, форма `repair.order`) → «Створити пропозицію» (`action_create_sale_order` ядра, `addons/repair/models/repair.py:447`, створення —
`:708` `sale.order.create`): під fitter (група «Сервіс» `td_mebli_claim.group_service`, `project.group_project_user`) і під store (`stock.group_stock_manager`) —
діалог «Помилка доступу: Ви не можете створювати записи 'Замовлення на продаж' (sale.order). Ця операція доступна наступним групам: - Продажі/Адміністратор
- Продажі/Користувач: Лише власні документи». Відтворено в UI (Playwright) і XML-RPC на WH/RO/00004 (fitter) і WH/RO/00003 (store) після зняття «На гарантії».
`group_service` включає лише `stock.group_stock_user` (`td_mebli_claim/security/security.xml:6-11`); у демо рекламація після гарантії (WH/RO/00005) має
пропозицію S00124 — створена наповненням не під роллю, тому сценарій T-06 це не ловив. За AC-112 «сервіс створює пропозицію ремонту». Маршрут: A-11
(`td_mebli_claim`): `action_create_sale_order` — перевірка права на рекламацію, створення пропозиції `sudo` з продавцем замовлення рекламації (як «Повторне
виготовлення», D-08), або група продажу в `group_service` (рішення A-08); кнопку не показувати ролям без «Сервісу» (store бачить її, отримує ту саму помилку).
Тест — під сервісом: пропозиція створюється, «На гарантії» вимкнено.

## A-16-5 (2026-11-15) — стенд A-15-full-2 `15dbd6f`: D-19…D-21 перевірено під ролями, нових дефектів немає
Повтор турів T-01…T-16 (як A-16-4) і перевірка дефектів A-16b під salon / tech / fitter / store: FAIL 0 (`scenarios.md` «Спроба 5»). D-19 (менеджер планує виїзд
у «Календар монтажів» з «Продажів»), D-20 (група «Технолог»: правила деталей і шаблони імпорту), D-21 (сервіс створює пропозицію ремонту, store кнопки не бачить) —
закрито; D-18 закрито в A-15-full-2. Рішення — AI-25…AI-28. AC-096 PDF плану дня на кілька днів — обмеження wkhtmltopdf середовища тесту (unpatched Qt), не дефект.
Повернення на A-14 немає. Далі — A-16b refresh (перезняти SC-03-2/4 і кадри ролей salon/tech/fitter за новими правами).

## A-16-6 (2026-11-16) — стенд A-15-full-3 `dd1c949`: повтор турів + головний екран A-11-fix4, нових дефектів немає
Тури T-01…T-16 — 114 PASS, 0 FAIL, 18 SKIP (`scenarios.md` «Спроба 6»); T-14 HM-01…HM-12 — PASS. Повернення на A-14 немає.

## D-22 — модуль (UI) — низький — A-11: «Код BAS» працівника без підпису — **ЗАКРИТО: неактуально — BAS виключено рішенням власника 2026-11-16** (A-16b-5/A-16b-6; поле `td_bas_code` разом з модулем `td_mebli_bas` з пакета видалено, на формі працівника його немає; було: відкрито A-16b-4)
Де: форма працівника, вкладка «Налаштування», блок «Відвідування/точка продажу»; `td_mebli_bas/views/document_views.xml:29-31` ставить `td_bas_code` після `barcode`, який у формі Odoo 19 стоїть у рядку з кнопкою «Друк значка» — поле виходить другим значенням рядка «Номер RFID/бейджа» без власного підпису (кадр `package/docs/user-guide/img/setup/SET-10.png`: «0001  П-0003»).
Очікувано: окремий рядок «Код BAS» з підписом (як у контрагента й варіанта товару). Обхід: `setup.md` § Працівники: код BAS і PIN цеху пояснює, яке значення — код. Маршрут: A-11 → A-14 → A-15 → A-16b (перезняти SET-10). Блокує прийняття: ні (на рішення власника).

## D-23 — модуль (права) — високий — A-11: технолог не міг створювати товари, специфікації, робочі центри — **ЗАКРИТО (A-11-fix5, `td_mebli_mrp` 19.0.1.1.6; рішення власника 2026-11-16 (права технолога; `flow/decisions.md` рядок 54))**
Джерело: незалежний аудит `setup.md` @2ef77fa (вердикт GAPS, пункт А; передано менеджерською сесією 2026-11-16).
Де: група «Технолог» (`td_mebli_mrp.group_technologist` = `mrp.group_mrp_user` + `stock.group_stock_user`) мала лише читання на `product.template`, `product.product`, `mrp.bom`, `mrp.bom.line`, `mrp.routing.workcenter`, `mrp.workcenter`, `mrp.workcenter.capacity`, атрибутах шаблону (Odoo 19 `mrp/security/ir.model.access.csv:6-9,20,53`; `product/security/ir.model.access.csv:12-14`), а `setup.md` доручав їх технологу (на кадрах SET-21, 23, 31, 32, 35, 36 — без «Новий»).
Виправлено за рішенням власника 2026-11-16 (права технолога): ACL групи «Технолог» у `td_mebli_mrp/security/ir.model.access.csv` — читання/запис/створення без видалення на 9 моделях власника + `resource.resource` (технічно, AI-39); «Виключити для» і будь-яке видалення — адміністратор; тест `test_d23_technologist_prepares_products_and_specifications`; перевірено на стенді під `tech` (A-16b-5) і перезнято кадри технолога.

## D-24 — модуль (права) — середній — A-11: технолог не міг вносити несумісні значення «Виключити для» — **ЗАКРИТО (A-11-fix6, `td_mebli_mrp` 19.0.1.1.7; рішення власника 2026-11-16, `flow/decisions.md` рядок 57)**
Джерело: відкрите питання A-16b-5 (`tests/open-questions.md`; AI-39 п. 2) — рішення власника 2026-11-16 передано менеджерською сесією.
Де: `product.template.attribute.exclusion` («Виключити для» значення виробу) — у групи «Технолог» не було прав; видалення товарів, специфікацій, операцій, робочих центрів і виключень — лише адміністратор, технолог архівує.
Виправлено: ACL `access_td_tech_ptae` (читання/запис/створення без видалення); збереження виключення перебудовує варіанти виробу (`product.template._create_variant_ids`) — неможливі варіанти для технолога архівуються замість видалення (`td_mebli_mrp` `product.product._unlink_or_archive`, AI-43); тест `test_d24_technologist_keeps_exclusions_and_archives` (форма значення → «Виключити для» → збереження; зміна; видалення — AccessError; архівування товару, специфікації, операції, робочого центру). Стенд під `tech@demo-fabryka.example` — A-16b-6. Код повернення: A-11 (закрито).
