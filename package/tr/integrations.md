# Інтеграції: обмін з BAS/BAF (`td_mebli_bas`), курс НБУ (`td_mebli_ua`), `l10n_ua` і ПДВ

AC: AC-037…AC-042, AC-078, AC-109, AC-N.03. Параметри анкети (SPEC §11): обмін з BAS — VP-04 (`td_mebli_bas` ставиться лише при `true`), курс НБУ — значення `nbu` VP-02, ПДВ — VP-18. Рішення: №5 (облік у BAS/BAF клієнта + наш обмін, запис 10), AI-13, AI-15, AI-A08-09…AI-A08-11. Формат обміну — **відкрите питання до франчайзі (ВП-1)**: цей розділ фіксує нашу сторону (черга, журнал, правила), а не формат BAS.

## 1. `td_mebli_bas` — обмін (новий)

### 1.1. Контракт (варіант 1, BOX §6)
| Напрям | Що | Коли | Ключ зіставлення |
|---|---|---|---|
| Odoo → BAS | контрагенти й номенклатура (майстер — Odoo), рахунки й реалізації покупцям (проведені `account.move` `out_invoice`/`out_refund`), закупівлі матеріалів (`in_invoice`), підтверджені нарахування й табель | щодня (cron) і кнопкою | зовнішній код BAS на довіднику (`td_bas_code`); номер документа Odoo |
| BAS → Odoo | оплати покупців і постачальникам (банк — у BAS, AI-15), статус ПН | щодня і кнопкою | номер рахунку Odoo в призначенні / полі пакета |
| Не обмінюємо | ПН/ЄРПН, ТТН, видаткові (друкуються в BAS) | — | — |

Кілька юросіб (B): окремий канал на кожну компанію (`td.mebli.bas.channel.company_id`); коробка A — один канал.

### 1.2. Моделі

**`td.mebli.bas.channel`** (налаштування каналу): `name`, `company_id` (required, правило multi-company), `transport` (selection: `file` «Файл у теці / вкладення» / `http` «HTTP-сервіс BAS»), `endpoint` (char, для `http`), `api_key` (char, `groups='base.group_system'`), `schema_version` (char — версія нашої схеми JSON до контракту), `active`, `last_run` (datetime).

**`td.mebli.bas.batch`** (пакет обміну): `channel_id`, `company_id` (related, store), `direction` (out / in), `kind` (selection: довідники / продажі / закупівлі / оплати / нарахування / табель), `state` (чернетка / надіслано / прийнято / помилка), `attachment_id` (m2o `ir.attachment` — файл пакета), `line_count`, `error_count`, `date`.

**`td.mebli.bas.log`** (рядок журналу): `batch_id`, `res_model` (char), `res_id` (`Many2oneReference` за `res_model` — `odoo/orm/fields_reference.py:59`), `state` (передано / помилка / не зіставлено), `message` (text).

**Поля на стандартних моделях:**

| Модель / поле | Тип | Примітка |
|---|---|---|
| `res.partner.td_bas_code`, `product.product.td_bas_code`, `hr.employee.td_bas_code` | char, index, `company_dependent=True` (`odoo/orm/fields.py:291`) — у кожної юрособи своя база BAS | зовнішній код; міграція зберігає коди (BOX §4) |
| `account.move.td_bas_state` | selection: — / передано / помилка, readonly, tracking | AC-039, AC-040 |
| `account.move.td_bas_batch_id` | m2o `td.mebli.bas.batch`, readonly | — |
| `sale.order.td_bas_state` | selection compute з рахунків замовлення | **заміняє** поле-імітацію зрізу в `td_mebli_ua` (R-06), міграція значень не потрібна |
| `td.mebli.accrual.bas_state` | див. `td_mebli_install.md` | AC-109 |

### 1.3. Правила
1. Документ із `td_bas_state = 'sent'` — `write` на суму, партнера, рядки або `button_draft` → UserError «Документ уже передано в BAS — виправлення лише сторно» (AC-041); дозволено лише стандартне сторно (`out_refund`).
2. Помилка одного документа не зупиняє пакет; документ отримує `error` і рядок журналу з причиною; кнопка «Повторити» (`group_finance`) (AC-040).
3. Вхідні оплати: створюється стандартна оплата (`account.payment`) і звіряється з рахунком за номером; не зіставлена — рядок журналу «Не зіставлено», активність фінансисту (AC-042). Після звірки скасовуються ручні позначки оплати того самого замовлення на ту саму суму (`td.mebli.pay.mark.cancelled`).
4. cron «Меблі: обмін з BAS» — щодня (`interval_type='days'`), час — параметр каналу.
5. Нашу сторону викликає BAS через HTTP (`/json/2/<модель>/<метод>` з ключем API — `odoo/addons/test_http/tests/test_webjson2.py:44`) або наш cron забирає/кладе файли. Остаточний варіант — після ВП-1.

### 1.4. UI
Меню «Облік → Обмін з BAS»: канали, пакети (`<list>` зі станом), журнал з фільтром «Помилки». Кнопки «Передати в BAS» на замовленні (замінює імітацію зрізу) і на нарахуваннях, «Повторити» на пакеті.

## 2. `td_mebli_ua` — курс НБУ (B) — зріз
`res.currency.rate.td_source` (selection: `nbu` «НБУ» / `nbu_imitation` «НБУ (імітація)» / `manual`), метод `res.currency._td_cron_nbu()` і cron «НБУ: курси валют» (щодня). Завантаження — у стандартні `res.currency.rate` (`odoo/addons/base/models/res_currency.py:346`) для валют, активних у компанії. Помилка мережі або формату → курси не змінюються, `_logger` і активність фінансисту «Курс НБУ не оновлено» (AC-038). Онлайн — параметр `td_mebli_ua.nbu_online` (у зрізі вимкнено; формат API НБУ — перевірити наживо в A-11, ВП-5). Кнопка «Оновити ціни за курсом» (`group_finance`, `group_feature_nbu`): перераховує `price_unit` лише пропозицій у стані `draft`/`sent` з товарами EUR-прайсу (стандартний `sale.order._recompute_prices` / «Оновити ціни» — `addons/sale/models/sale_order.py:1365`, `:1377`) і пише старий/новий підсумок у чат (AC-037).

## 3. `l10n_ua` і ПДВ (AI-A08-11)
- `l10n_ua` (CE, `addons/l10n_ua/__manifest__.py`: `depends: account`, `auto_install: ['account']`; план рахунків ПСБО з податками `sale_tax_template_vat20_psbo`, `purchase_tax_template_vat20_psbo` — `addons/l10n_ua/models/template_ua_psbo.py:33-34`) ставиться конфіг-пакетом A-12 для компанії з країною UA; наші модулі від нього не залежать.
- Податок товару — стандартні податки ПДВ 20 % (або «без ПДВ» для ФОП-неплатника — податок компанії ФОП у конфіг-пакеті). Ціни прайс-листа — «з ПДВ» або «без» — налаштування компанії «Ціни з податком / без» (`res.company.account_price_include`, `addons/account/models/company.py:272`) або податку (`price_include_override`, `addons/account/models/account_tax.py:142`), параметр анкети.
- Собівартість, маржа, ціна за історією, % бригаді — від сум **без ПДВ** (`amount_untaxed`, `price_subtotal`).
- ПН/ЄРПН — у BAS (рішення №5); ПРРО — сторонній модуль за потреби (BOX §10), поза пакетом.
