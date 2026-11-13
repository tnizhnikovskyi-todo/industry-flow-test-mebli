# Друковані форми (QWeb-PDF)

AC: AC-032, AC-033, AC-034, AC-061, AC-094, AC-096, AC-101, AC-102, AC-N.01, AC-N.06. Механізм — `ir.actions.report` з `report_type='qweb-pdf'` (`odoo/addons/base/models/ir_actions_report.py:171`), формат паперу `paperformat_id` (`:186`), макет документа компанії — `web.external_layout` (`addons/web/views/report_templates.xml`); синтаксис 19.0 — `t-out` (не `t-raw`). Шрифт з кирилицею — `td_mebli_base` (AC-N.06). Тексти договору й актів — **шаблон до перевірки юристом** (№17, ВП-2): позначка в колонтитулі, доки параметр компанії «Тексти перевірено юристом» (`res.company.td_legal_checked`, boolean — **нове**) не ввімкнено.

| Форма | Модуль | Модель (`model`) | Дія звіту (`report_name`) | Зміст | Коробка | Статус |
|---|---|---|---|---|---|---|
| КП / замовлення | стандарт `sale` + `td_mebli_sale` | `sale.order` | успадкування стандартного шаблону | + блок «Візуалізація проєкту» (`t-if="doc.td_design_image"`) | A | зріз (хвиля 2) |
| Договір (2 режими) | `td_mebli_sale` | `sale.order` | `td_mebli_sale.report_contract` | реквізити продавця, режим (`company_id.td_contract_mode`), вироби, графік оплат з етапів умов оплати, специфікація (додаток), підписи; без режиму — UserError (AC-034) | A | зріз |
| Рахунок на передоплату / доплату | стандарт `account` | `account.move` | стандарт | — | A | стандарт |
| Етикетки деталей з QR | `td_mebli_shop` | `mrp.production`, `sale.order` | `td_mebli_shop.report_part_labels` | деталь, Д×Ш, матеріал, замовлення, місце, QR коду `label`; формат 58×40 мм | A | зріз (хвиля 2) |
| Комплектувальний лист | `td_mebli_shop` | `sale.order` | `td_mebli_shop.report_kit` | місця, вид, деталь, кількість, «Зібрано», підпис | A | зріз |
| Акт монтажу (етапний / фінальний) | `td_mebli_install` | `td.mebli.install.act` | `td_mebli_install.report_act` | чек-лист, недоліки з фото, фото, підпис клієнта, ПІБ підписанта, дата | A | зріз |
| Акт приймання-передачі без монтажу | `td_mebli_install` | `stock.picking` (відвантаження замовлення) | `td_mebli_install.report_handover` | вироби, дата, підписи сторін | A | зріз (хвиля 2) |
| Денний план бригади | `td_mebli_install` | `project.task` (вибірка дня) | `td_mebli_install.report_day_plan` | час, замовлення, адреса, місця до завантаження, сума до отримання | A | зріз (хвиля 2) |
| Відомість нарахувань | `td_mebli_install` | `td.mebli.accrual` | `td_mebli_install.report_accruals` | лише підтверджені; працівник, вид, сума, причина, підсумки; підпис керівника (AC-134) | A | **нове** |
| Наряд на замовлення (паперовий резерв при відключенні світла) | `td_mebli_shop` | `mrp.production` | `td_mebli_shop.report_work_order` | операції, деталі з QR, поля відміток (AC-133) | A | **нове** (BOX §8 п. 8) |
| Список деталей на порізку (PDF до CSV) | `td_mebli_cutting` | `td.mebli.cutting.job` | `td_mebli_cutting.report_cutting_list` | версія специфікації, деталі, кромка | A | **нове** |
| Додаткова угода на зміну, гарантійний документ, акт рекламації | `td_mebli_sale`, `td_mebli_install`, `td_mebli_claim` | — | — | після юриста | B | поза першою хвилею A-11 |

Друк з кнопок форм і меню «Друк» (`binding_model_id`); видаткові, ТТН, податкові — у BAS (BOX §11.2, G-83). Мова друку — мова партнера (`lang`), за замовчуванням `uk_UA`.
